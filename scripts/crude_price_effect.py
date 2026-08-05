"""scripts/crude_price_effect.py — effect of the corrected crude-oil price.

The PCA bulletin of 31 July 2026 gives domestic millgate crude coconut oil at
100.8 to 125.44 PHP/kg against a modelled 140.0, so the crude-bypass option is
worth 12 to 39 percent less than the campaign assumed. That correction acts on the
value of ONE option during disruption, not on the nominal baseline, so it cannot
be propagated by scaling the reported economics.

This measures it directly. For each scenario, the crude-bypass option is run
against the null arm at both prices on identical disruption paths, so the
difference is the price effect and nothing else.

The interesting question is not how much the option is worth less, which is known
by construction, but how much dR falls. A selection layer that can decline the
option is partly protected: if the corrected price makes the bypass unattractive,
the system stops choosing it and loses only the value it would have added, not the
value it now destroys. That is a testable claim about whether adaptivity buffers a
parameter error, and it is what this script reports.

Usage:
    python scripts/crude_price_effect.py --cats D1,D3,D4,D8 --n 60
"""
import argparse, importlib.util, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401
import numpy as np, pandas as pd

SEED0 = 31415
W_MODELLED = 140.0
W_LOW, W_HIGH = 100.8, 125.44          # PCA 31-Jul-2026 domestic millgate range
W_MID = 0.5 * (W_LOW + W_HIGH)


def _gp():
    spec = importlib.util.spec_from_file_location(
        "gp", pathlib.Path(__file__).parent / "gen_pilot.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def run(cats, n):
    import casadi as ca
    from rdt_core.plant_dae import PlantParams, build_plant_dae, wb2db
    from rdt_core.disruptions import sample
    gp = _gp()
    rows = []
    for w in (W_MODELLED, W_HIGH, W_MID, W_LOW):
        p = PlantParams(w_crude=w)
        dae, out_fn = build_plant_dae(p)
        intg = ca.integrator("P", "idas", dae, 0.0, gp.DT,
                             {"abstol": 1e-8, "reltol": 1e-8})
        F0 = p.nominal_nut_feed()
        x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                             [F0 * 0.30 * p.tau_buf * 0.8, 2000., 3000., 1000.],
                             [0, 0]])
        z0 = np.zeros(2)
        for cat in cats:
            t0 = time.perf_counter()
            for dp in sample(cat, n, SEED0):
                try:
                    _, R0, _, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x0, z0)
                    _, R1, _, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x0, z0,
                                                u_crude=1.0)
                except RuntimeError:
                    continue
                rows.append(dict(w_crude=w, category=cat, seed=dp.seed,
                                 duration_hr=dp.duration_hr,
                                 dR_option=R1 - R0,
                                 dR_selective=max(0.0, R1 - R0)))
            print(f"  w_crude={w:6.2f} {cat} {time.perf_counter()-t0:4.0f}s", flush=True)
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cats", default="D1,D3,D4,D8")
    ap.add_argument("--n", type=int, default=60)
    a = ap.parse_args()
    d = run(a.cats.split(","), a.n)
    d.to_csv("data/crude_price_effect.csv", index=False)

    print("\nCRUDE-BYPASS OPTION VALUE AT THE MODELLED AND OBSERVED PRICES")
    print("dR_option    always activating the option (no selection)")
    print("dR_selective a selection layer that declines the option when it hurts\n")
    hdr = f"{'w_crude':>9} {'basis':<22} {'dR_option':>11} {'dR_select':>11} {'harm rate':>10}"
    print(hdr); print("-" * len(hdr))
    base_o = base_s = None
    for w, lab in [(W_MODELLED, "modelled"), (W_HIGH, "PCA upper 125.44"),
                   (W_MID, "PCA midpoint"), (W_LOW, "PCA lower 100.80")]:
        s = d[np.isclose(d.w_crude, w)]
        if not len(s):
            continue
        o, sel = s.dR_option.mean(), s.dR_selective.mean()
        harm = float((s.dR_option < 0).mean())
        if base_o is None:
            base_o, base_s = o, sel
        print(f"{w:9.2f} {lab:<22} {o:11.5f} {sel:11.5f} {harm:10.1%}")

    lo = d[np.isclose(d.w_crude, W_LOW)]
    if len(lo) and base_o:
        o, sel = lo.dR_option.mean(), lo.dR_selective.mean()
        print(f"\nAt the lowest observed price, {W_LOW} PHP/kg:")
        print(f"  always-activate option value falls {100*(1-o/base_o):5.1f}% "
              f"({base_o:.5f} to {o:.5f})")
        print(f"  with selection it falls           {100*(1-sel/base_s):5.1f}% "
              f"({base_s:.5f} to {sel:.5f})")
        print("\n  The gap between those two figures is the protection a selection")
        print("  layer provides against this parameter error. The closed-loop dR")
        print("  correction lies at or below the selective figure, because the")
        print("  full system also has other options to substitute toward.")
    print("\nwrote data/crude_price_effect.csv")


if __name__ == "__main__":
    main()
