"""scripts/closed_loop_eval.py — First end-to-end closed-loop ΔR (H4 miniature).

Screen: HistGBT on STATE-ONLY features (flattened X_V+X_E+dG, dataset v1) — the
deployable 0.62-R² model, NOT the oracle-informed one. Trained on SEED0=31415
label scenarios; evaluated on FRESH draws SEED=27182 (scenario-disjoint).
Usage: python scripts/closed_loop_eval.py <category>
"""
import sys, time, pathlib, pickle
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from rdt_core.plant_dae import PlantParams, wb2db
from rdt_core.disruptions import sample
from rdt_core.loop import TopologyCache, run_closed_loop
from rdt_core import features as ft

SEED_EVAL, N_EVAL = 27182, 40
import os
SLICE = os.environ.get("SLICE", "")  # "0:20" style chunking for call budget
MODEL_PATH = pathlib.Path("data/gbt_screen_v1.pkl")


def get_screen():
    if MODEL_PATH.exists():
        model = pickle.loads(MODEL_PATH.read_bytes())
    else:
        from sklearn.ensemble import HistGradientBoostingRegressor
        d = np.load("data/gat_dataset_v1.npz", allow_pickle=True)
        X = np.concatenate([d["X_V"].reshape(len(d["y"]), -1),
                            d["X_E"].reshape(len(d["y"]), -1), d["dG"]], 1)
        model = HistGradientBoostingRegressor(random_state=0).fit(X, d["y"])
        MODEL_PATH.write_bytes(pickle.dumps(model))
        print(f"screen trained on {len(d['y'])} labels -> {MODEL_PATH}")
    def screen(Xv, Xe, dG_rows):
        base = np.concatenate([Xv.ravel(), Xe.ravel()])
        Xq = np.stack([np.concatenate([base, dg]) for dg in dG_rows])
        return model.predict(Xq)
    return screen


def main(cat):
    p = PlantParams(); F0 = p.nominal_nut_feed()
    cache = TopologyCache(p)
    screen = get_screen()
    x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                         [F0 * 0.30 * p.tau_buf * 0.8, 2000.0, 3000.0, 1000.0], [0, 0]])
    rows, t0 = [], time.perf_counter()
    dps = sample(cat, N_EVAL, SEED_EVAL)
    if SLICE:
        a, b = map(int, SLICE.split(":")); dps = dps[a:b]
    for dp in dps:
        R_s, _, _ = run_closed_loop(dp, None, cache, F0, x0, static=True)
        R_r, sw, log = run_closed_loop(dp, screen, cache, F0, x0)
        rows.append(dict(category=cat, seed=dp.seed, unit=dp.unit,
                         severity=dp.severity, duration_hr=dp.duration_hr,
                         R_static=R_s, R_rdt=R_r, dR=R_r - R_s, n_switches=sw,
                         data_class="SYNTHETIC/physics-forward-model"))
    df = pd.DataFrame(rows)
    out = pathlib.Path("data/closed_loop_v1.parquet")
    if out.exists():
        df = pd.concat([pd.read_parquet(out), df], ignore_index=True)
    df.to_parquet(out, index=False)
    g = df[df.category == cat]
    print(f"{cat}: {len(g)} paired runs, {time.perf_counter()-t0:.0f} s | "
          f"dR mean={g.dR.mean():.4f} p5={g.dR.quantile(.05):.4f} "
          f"p95={g.dR.quantile(.95):.4f} | switches med={g.n_switches.median():.0f}")


if __name__ == "__main__":
    main(sys.argv[1])
