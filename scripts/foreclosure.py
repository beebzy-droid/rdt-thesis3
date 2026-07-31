"""scripts/foreclosure.py — does perishability foreclose the buffering strategy?

The reframed claim (thesis/theory_transition_dynamics.md and the related-work
positioning) is that buffering and reconfiguration are not merely substitutable
resilience mechanisms, as the supply-chain literature has held since Tomlin
(2006), but that for a PERISHABLE intermediate the substitution collapses into a
foreclosure: beyond a shelf-life-determined disruption duration, additional buffer
buys nothing, because the stock degrades before it can be drawn.

Tomlin already showed that longer disruptions favour sourcing over inventory. The
distinction being tested here is stronger and physical rather than economic: not
that buffering becomes less attractive, but that it stops working at all.

DESIGN. Pre-position copra inventory at multiples of the nominal level, run the
plant with NO reconfiguration available, and measure the resilience integral
against disruption duration, under two contracts:

  tau_shelf = 0    stored copra keeps indefinitely (the historical model)
  tau_shelf > 0    stored copra degrades toward the aflatoxin-risk threshold

FALSIFIABLE PREDICTION. The marginal value of buffer, dR/d(buffer multiple), is
positive at all durations when copra keeps, and falls toward zero for durations
well beyond tau_shelf when it does not. If the marginal value stays positive at
long durations under perishability, the foreclosure claim is wrong and the
mechanism is ordinary economic substitution.

CONTROL. Reconfiguration (copra purchase, the supply-disruption rescue) is run
separately at nominal buffer so its marginal value can be compared on the same
scenarios. The claim requires that reconfiguration keeps paying where buffer
stops.

Usage:
    python scripts/foreclosure.py --shelf 0,336 --mults 1,2,4,8 --n 60
    python scripts/foreclosure.py --analyze
"""
import argparse
import glob
import importlib.util
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401

import numpy as np
import pandas as pd

SEED0 = 31415
OUT = pathlib.Path("data/foreclosure")


def _gp():
    spec = importlib.util.spec_from_file_location(
        "gp", pathlib.Path(__file__).parent / "gen_pilot.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def run_cell(job):
    shelf, mult, cat, n_scen = job
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"shelf{shelf:06.1f}_m{mult:04.1f}_{cat}.parquet"
    if out.exists():
        return f"shelf={shelf:6.1f} mult={mult:4.1f} {cat} skip"

    import casadi as ca
    from rdt_core.plant_dae import PlantParams, build_plant_dae, wb2db
    from rdt_core.disruptions import sample
    gp = _gp()

    p = PlantParams(tau_shelf=float(shelf))
    dae, out_fn = build_plant_dae(p)
    intg = ca.integrator("P", "idas", dae, 0.0, gp.DT,
                         {"abstol": 1e-8, "reltol": 1e-8})
    F0 = p.nominal_nut_feed()
    base_buf = F0 * 0.30 * p.tau_buf * 0.8
    x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                         [base_buf * float(mult), 2000.0, 3000.0, 1000.0],
                         [0, 0]])
    z0 = np.zeros(2)

    rows, skipped = [], 0
    t0 = time.perf_counter()
    for dp in sample(cat, n_scen, SEED0):
        try:
            # Buffer arm: extra pre-positioned stock, NO reconfiguration
            _, R_buf, _, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x0, z0)
            # Reconfiguration arm: nominal stock, purchase option available
            x_nom = x0.copy(); x_nom[5] = base_buf
            _, R_rec, _, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x_nom, z0,
                                           u_buy=1.0)
            _, R_nul, _, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x_nom, z0)
        except RuntimeError:
            skipped += 1
            continue
        rows.append(dict(tau_shelf=float(shelf), buffer_mult=float(mult),
                         category=cat, seed=dp.seed, duration_hr=dp.duration_hr,
                         severity=dp.severity, R_buffer=R_buf,
                         R_reconfig=R_rec, R_null=R_nul,
                         data_class="SYNTHETIC/physics-forward-model"))
    pd.DataFrame(rows).to_parquet(out, index=False)
    return (f"shelf={shelf:6.1f} mult={mult:4.1f} {cat} done {len(rows):3d} "
            f"({skipped} skipped) {time.perf_counter()-t0:4.0f}s")


def analyze():
    files = sorted(glob.glob(str(OUT / "*.parquet")))
    if not files:
        sys.exit("no foreclosure shards; run without --analyze first")
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    print(f"loaded {len(d)} runs | shelf contracts {sorted(d.tau_shelf.unique())} "
          f"| buffer multiples {sorted(d.buffer_mult.unique())}\n")

    # marginal value of buffer within duration bins, per shelf contract
    bins = [(0, 24), (24, 72), (72, 168), (168, 1e9)]
    labels = ["<1 d", "1-3 d", "3-7 d", ">7 d"]
    print("MARGINAL VALUE OF PRE-POSITIONED BUFFER, dR / d(buffer multiple)")
    print("Prediction: positive at all durations when copra keeps; falling to zero")
    print("beyond the shelf life when it does not.\n")
    hdr = f"{'shelf life':>14} " + " ".join(f"{l:>10}" for l in labels)
    print(hdr); print("-" * len(hdr))
    for shelf in sorted(d.tau_shelf.unique()):
        cells = []
        for lo, hi in bins:
            s = d[(d.tau_shelf == shelf) & (d.duration_hr >= lo)
                  & (d.duration_hr < hi)]
            if s.buffer_mult.nunique() >= 2 and len(s) >= 8:
                sl = np.polyfit(s.buffer_mult, s.R_buffer, 1)[0]
                cells.append(f"{sl:+10.5f}")
            else:
                cells.append(f"{'n/a':>10}")
        tag = "keeps" if shelf == 0 else f"{shelf/24:.0f} d"
        print(f"{tag:>14} " + " ".join(cells))

    # control: does reconfiguration keep paying where buffer stops?
    print("\nCONTROL, reconfiguration gain over null at nominal buffer "
          "(mean dR by duration)")
    hdr2 = f"{'shelf life':>14} " + " ".join(f"{l:>10}" for l in labels)
    print(hdr2); print("-" * len(hdr2))
    for shelf in sorted(d.tau_shelf.unique()):
        cells = []
        for lo, hi in bins:
            s = d[(d.tau_shelf == shelf) & (d.duration_hr >= lo)
                  & (d.duration_hr < hi) & (d.buffer_mult == d.buffer_mult.min())]
            cells.append(f"{(s.R_reconfig - s.R_null).mean():+10.5f}"
                         if len(s) >= 5 else f"{'n/a':>10}")
        tag = "keeps" if shelf == 0 else f"{shelf/24:.0f} d"
        print(f"{tag:>14} " + " ".join(cells))

    d.to_csv("data/foreclosure_runs.csv", index=False)
    print("\nwrote data/foreclosure_runs.csv")
    print("\nREADING: foreclosure requires the buffer row to decay toward zero "
          "under a\nfinite shelf life while the reconfiguration row does not. "
          "If both persist,\nthe mechanism is ordinary substitution and the "
          "claim fails.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shelf", default="0,336")
    ap.add_argument("--mults", default="1,2,4,8")
    ap.add_argument("--cats", default="D1")
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.analyze:
        analyze(); return
    jobs = [(float(s), float(m), c, a.n)
            for s in a.shelf.split(",") for m in a.mults.split(",")
            for c in a.cats.split(",")]
    print(f"{len(jobs)} cells")
    for j in jobs:
        print(run_cell(j), flush=True)
    print("\nnow run: python scripts/foreclosure.py --analyze")


if __name__ == "__main__":
    main()
