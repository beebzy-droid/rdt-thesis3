"""scripts/demo_reconfig.py — FIRST PAIRED ΔR MEASUREMENT (H4 protocol miniature).

Design: 60 D3 unit-failure scenarios (20 per failed unit: dry/press/refine),
each executed under two arms on IDENTICAL parameters (CRN by determinism):
  static arm : u_crude = 0  (twin cannot reconfigure)
  RDT arm    : u_crude = 1  (crude-VCO sale bypass active when refining is down)
ΔR = R_php(RDT) − R_php(static), Eq. 2.17 on the value basis.
Expected structure: ΔR > 0 for refine failures only; ≈ 0 for dry/press —
the dose-response-by-unit sanity check.
"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import casadi as ca
import importlib.util

from rdt_core.plant_dae import PlantParams, build_plant_dae, wb2db
from rdt_core.disruptions import sample

spec = importlib.util.spec_from_file_location("gp", pathlib.Path(__file__).parent / "gen_pilot.py")
gp = importlib.util.module_from_spec(spec); spec.loader.exec_module(gp)

p = PlantParams()
dae, out_fn = build_plant_dae(p)
intg = ca.integrator("P", "idas", dae, 0.0, gp.DT, {"abstol": 1e-8, "reltol": 1e-8})
F0 = p.nominal_nut_feed()
x_in = wb2db(p.x_in_wb)
x0 = np.concatenate([np.full(5, x_in),
                     [F0 * 0.30 * p.tau_buf * 0.8, 2000.0, 3000.0, 1000.0], [0, 0]])
z0 = np.zeros(2)

rows, t0 = [], time.perf_counter()
for dp in sample("D3", 60, 42):
    _, R0, ttr0, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x0, z0, u_crude=0.0)
    _, R1, ttr1, _, _ = gp.run_one(dp, p, intg, out_fn, F0, x0, z0, u_crude=1.0)
    rows.append((dp.unit, dp.duration_hr, R0, R1, R1 - R0, ttr0, ttr1))
print(f"120 paired runs in {time.perf_counter()-t0:.0f} s")

import pandas as pd
df = pd.DataFrame(rows, columns=["unit", "dur_hr", "R_static", "R_rdt", "dR", "TTR0", "TTR1"])
df.to_parquet("data/demo_paired_d3.parquet", index=False)
print(df.groupby("unit").agg(n=("dR", "size"), R_static=("R_static", "mean"),
                             R_rdt=("R_rdt", "mean"), dR_mean=("dR", "mean"),
                             dR_min=("dR", "min"), dR_max=("dR", "max")).round(4).to_string())

# bootstrap 95% CI on ΔR for refine-failure subgroup (the treated stratum)
ref = df[df.unit == "refine"]["dR"].to_numpy()
rng = np.random.default_rng(0)
bs = np.array([rng.choice(ref, ref.size).mean() for _ in range(10_000)])
print(f"refine stratum: mean ΔR = {ref.mean():.4f}, "
      f"bootstrap 95% CI [{np.percentile(bs,2.5):.4f}, {np.percentile(bs,97.5):.4f}]")
