"""scripts/tau_dry_sensitivity.py — is the headline sensitive to dryer residence?

tau_dry is the last E11-critical parameter without a verified value. The modelled
30 h sits between the authoritative Philippine mechanical figure of about 24 h
(PCA Zamboanga Research Center / DOST-PCAARRD) and roughly 36 h for small-holder
indirect dryers.

Rather than argue about the value first, measure whether it matters. If the
resilience gain is insensitive across the documented envelope, the verification
burden collapses and that is reportable; if it is sensitive, the sourcing has to
be done properly before anything is claimed.

Method. For each scenario the null arm and every available option are run on
identical disruption paths at each tau, and the per-scenario best option is taken.
That upper envelope is the one-shot oracle, which bounds what any selection layer
could achieve and is therefore the right quantity for a sensitivity test: if the
oracle gain does not move with tau, no realizable policy's gain can move much
either.

Note tau_dry is applied to BOTH arms, because dryer residence is plant physics and
not a property of the treatment.

Usage: python scripts/tau_dry_sensitivity.py --taus 24,30,36 --cats D3,D4 --n 25
"""
import argparse, importlib.util, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401
import numpy as np, pandas as pd

SEED0 = 31415
OPTIONS = {"crude_bypass": dict(u_crude=1.0),
           "wet_route":    dict(u_wet=1.0),
           "copra_buy":    dict(u_buy=1.0)}


def _gp():
    spec = importlib.util.spec_from_file_location(
        "gp", pathlib.Path(__file__).parent / "gen_pilot.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--taus", default="24,30,36")
    ap.add_argument("--cats", default="D3,D4")
    ap.add_argument("--n", type=int, default=25)
    a = ap.parse_args()

    import casadi as ca
    from rdt_core.plant_dae import PlantParams, build_plant_dae, wb2db
    from rdt_core.disruptions import sample
    gp = _gp()
    rows = []
    for tau in [float(t) for t in a.taus.split(",")]:
        p = PlantParams(tau_dry=tau)
        dae, out_fn = build_plant_dae(p)
        intg = ca.integrator("P", "idas", dae, 0.0, gp.DT,
                             {"abstol": 1e-8, "reltol": 1e-8})
        F0 = p.nominal_nut_feed()
        x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                             [F0 * 0.30 * p.tau_buf * 0.8, 2000., 3000., 1000.],
                             [0, 0]])
        z0 = np.zeros(2)
        for cat in a.cats.split(","):
            t0 = time.perf_counter()
            for dp in sample(cat, a.n, SEED0):
                try:
                    _, R0, _, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x0, z0)
                    best = R0
                    for u in OPTIONS.values():
                        _, R1, _, _, _ = gp.run_one(dp, p, intg, out_fn,
                                                    F0, x0, z0, **u)
                        best = max(best, R1)
                except RuntimeError:
                    continue
                rows.append(dict(tau_dry=tau, category=cat, seed=dp.seed,
                                 R_null=R0, R_oracle=best, dR=best - R0))
            print(f"  tau={tau:5.1f} {cat} {time.perf_counter()-t0:4.0f}s", flush=True)

    d = pd.DataFrame(rows)
    d.to_csv("data/tau_dry_sensitivity.csv", index=False)
    print("\nORACLE RESILIENCE GAIN ACROSS THE DOCUMENTED tau_dry ENVELOPE")
    print("(upper bound on any selection policy; if this does not move, "
          "no realizable policy's gain moves much)\n")
    hdr = f"{'tau_dry':>9} {'R_null':>9} {'R_oracle':>10} {'dR':>9} {'n':>5}"
    print(hdr); print("-" * len(hdr))
    for tau in sorted(d.tau_dry.unique()):
        s = d[d.tau_dry == tau]
        print(f"{tau:9.1f} {s.R_null.mean():9.4f} {s.R_oracle.mean():10.4f} "
              f"{s.dR.mean():9.4f} {len(s):5d}")
    lo, hi = d.tau_dry.min(), d.tau_dry.max()
    a_lo, a_hi = d[d.tau_dry == lo].dR.mean(), d[d.tau_dry == hi].dR.mean()
    span = abs(a_hi - a_lo)
    print(f"\nspan across {lo:.0f} to {hi:.0f} h: {span:.4f} in dR "
          f"({100*span/max(a_lo, 1e-9):.1f}% of the value at {lo:.0f} h)")
    print("\nInterpretation: a span small relative to the reported dR of 0.244")
    print("means the headline does not depend on resolving tau_dry, and the")
    print("parameter can be reported as a documented range rather than pinned.")


if __name__ == "__main__":
    main()
