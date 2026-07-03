"""scripts/gen_labels.py — Label pipeline v0 (lifecycle Phase 2, §5.2.1 miniature).

For each disruption scenario (D1/D3/D4/D8) and each ΔG option in the actionable set
{crude_bypass, wet_route, copra_buy}, run PAIRED simulations (option vs null, identical
parameters — CRN by determinism) and record the impact labels:
    dR_php   = R72_php(option) − R72_php(null)      [primary GAT regression target]
    dTTR80   = TTR80(option) − TTR80(null)          [hr; NaN-safe]
Structural feasibility: all three options are single-edge activations verified feasible
by tests/test_gates (each_option_activation) — feasibility labels become non-trivial
with the full topology-DAE.

Usage: python scripts/gen_labels.py D1 [--append]      (chunked per category)
Output: data/labels_v0.parquet  (data_class=SYNTHETIC/physics-forward-model)
"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import casadi as ca
import importlib.util

from rdt_core.plant_dae import PlantParams, build_plant_dae, wb2db
from rdt_core.disruptions import sample

spec = importlib.util.spec_from_file_location("gp", pathlib.Path(__file__).parent / "gen_pilot.py")
gp = importlib.util.module_from_spec(spec); spec.loader.exec_module(gp)

OPTIONS = {"crude_bypass": dict(u_crude=1.0),
           "wet_route":    dict(u_wet=1.0),
           "copra_buy":    dict(u_buy=1.0)}
N_PER_CAT = 40
SEED0 = 31415


def main(cat: str, append: bool):
    p = PlantParams()
    dae, out_fn = build_plant_dae(p)
    intg = ca.integrator("P", "idas", dae, 0.0, gp.DT, {"abstol": 1e-8, "reltol": 1e-8})
    F0 = p.nominal_nut_feed()
    x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                         [F0 * 0.30 * p.tau_buf * 0.8, 2000.0, 3000.0, 1000.0], [0, 0]])
    z0 = np.zeros(2)

    rows, t0 = [], time.perf_counter()
    for dp in sample(cat, N_PER_CAT, SEED0):
        _, R0, ttr0, _, V0 = gp.run_one(dp, p, intg, out_fn, F0, x0, z0)
        for name, u in OPTIONS.items():
            _, R1, ttr1, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x0, z0, **u)
            d_ttr = (ttr1 - ttr0) if np.isfinite(ttr1) and np.isfinite(ttr0) else np.nan
            rows.append(dict(category=cat, seed=dp.seed, unit=dp.unit,
                             severity=dp.severity, duration_hr=dp.duration_hr,
                             onset_hr=dp.onset_hr, dx_wb=dp.dx_wb, y_mult=dp.y_mult,
                             option=name, R_null=R0, R_opt=R1, dR_php=R1 - R0,
                             dTTR80_hr=d_ttr, V0_php_hr=V0,
                             data_class="SYNTHETIC/physics-forward-model"))
    df = pd.DataFrame(rows)
    out = pathlib.Path("data/labels_v0.parquet")
    if append and out.exists():
        df = pd.concat([pd.read_parquet(out), df], ignore_index=True)
    df.to_parquet(out, index=False)
    n_new = len(rows)
    print(f"{cat}: {N_PER_CAT} scenarios × {1+len(OPTIONS)} arms = "
          f"{N_PER_CAT*(1+len(OPTIONS))} runs, {time.perf_counter()-t0:.0f} s "
          f"-> {n_new} labels (file total {len(df)})")


if __name__ == "__main__":
    main(sys.argv[1], "--append" in sys.argv)
