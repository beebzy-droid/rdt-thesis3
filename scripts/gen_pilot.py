"""scripts/gen_pilot.py — Static-twin BASELINE pilot library (lifecycle Phase 1 exit
prerequisite). For each sampled disruption: 30-day run, resilience integral R over
the 72-hr post-onset window (Eq. 2.16), and TTR80 (6-hr-sustained definition).

This IS the static-DT comparator distribution of H4/H5 — no reconfiguration occurs.
Output: data/pilot_baseline.parquet + per-category summary to stdout.
"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import casadi as ca

from rdt_core.plant_dae import PlantParams, build_plant_dae, wb2db
from rdt_core.disruptions import sample, dae_params, MAPPED_V0

DT = 0.5          # hr, event grid
DAYS = 30.0
R_WINDOW = 72.0   # hr, Eq. 2.16 horizon for Cat 1–2 class events
N_PER_CAT = 125
SEED0 = 20260703


def run_one(dp, p, intg, out_fn, F0, x0, z0):
    n = int(DAYS * 24 / DT)
    xk, zk = x0.copy(), z0.copy()
    t_grid = np.arange(1, n + 1) * DT
    P = np.empty(n)
    for i, t in enumerate(t_grid):
        par = dae_params(dp, t - DT, F0)              # piecewise-constant over step
        r = intg(x0=xk, z0=zk, p=par)
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        P[i] = float(out_fn(xk, zk, par))
    # nominal P0: mean over the pre-onset settled window (last 24 h before onset)
    pre = (t_grid > dp.onset_hr - 24) & (t_grid <= dp.onset_hr)
    P0 = P[pre].mean()
    win = (t_grid > dp.onset_hr) & (t_grid <= dp.onset_hr + R_WINDOW)
    R = float(np.mean(P[win] / P0))                   # Eq. 2.16, discrete
    # TTR80 (corrected 2026-07-03): time from onset to sustained (6 hr) return to
    # >= 0.8, measured only AFTER first impairment (ratio < 0.8). Never impaired
    # within window -> 0.0. Impaired and never returns in sim window -> NaN.
    ratio = P / P0
    post = np.where(t_grid > dp.onset_hr)[0]
    k6 = int(6 / DT)
    below = post[ratio[post] < 0.8]
    if below.size == 0:
        ttr80 = 0.0
    else:
        ttr80 = np.nan
        for j in post[post >= below[0]]:
            if j + k6 <= n and np.all(ratio[j:j + k6] >= 0.8):
                ttr80 = t_grid[j] - dp.onset_hr
                break
    return R, ttr80, P0


def main(categories=None, out_path="data/pilot_baseline.parquet", append=False):
    categories = categories or list(MAPPED_V0)
    p = PlantParams()
    dae, out_fn = build_plant_dae(p)
    intg = ca.integrator("P", "idas", dae, 0.0, DT, {"abstol": 1e-8, "reltol": 1e-8})
    F0 = p.nominal_nut_feed()
    x_in = wb2db(p.x_in_wb)
    x0 = np.concatenate([np.full(5, x_in),
                         [F0 * 0.30 * p.tau_buf * 0.8, 2000.0, 3000.0, 1000.0],
                         [0.0, 0.0]])
    z0 = np.zeros(2)

    rows, t0 = [], time.perf_counter()
    for cat in categories:
        for dp in sample(cat, N_PER_CAT, SEED0):
            R, ttr, P0 = run_one(dp, p, intg, out_fn, F0, x0, z0)
            rows.append(dict(category=cat, seed=dp.seed, severity=dp.severity,
                             onset_hr=dp.onset_hr, ramp_hr=dp.ramp_hr,
                             duration_hr=dp.duration_hr, tau_rec=dp.recovery_tau_hr,
                             dx_wb=dp.dx_wb, y_mult=dp.y_mult,
                             R72=R, TTR80_hr=ttr, P0_kg_hr=P0,
                             data_class="SYNTHETIC/physics-forward-model"))
    wall = time.perf_counter() - t0
    df = pd.DataFrame(rows)
    if append and pathlib.Path(out_path).exists():
        df = pd.concat([pd.read_parquet(out_path), df], ignore_index=True)
    df.to_parquet(out_path, index=False)

    print(f"pilot baseline library: {len(df)} runs in {wall:.1f} s "
          f"({wall/len(df)*1000:.0f} ms/run)")
    g = df.groupby("category").agg(
        n=("R72", "size"), R_mean=("R72", "mean"), R_p5=("R72", lambda s: s.quantile(.05)),
        R_p95=("R72", lambda s: s.quantile(.95)),
        TTR80_med=("TTR80_hr", "median"),
        frac_no_recovery=("TTR80_hr", lambda s: s.isna().mean()))
    print(g.round(3).to_string())


if __name__ == "__main__":
    cats = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    main(cats, append=len(sys.argv) > 2 and sys.argv[2] == "--append")
