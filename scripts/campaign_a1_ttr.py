"""scripts/campaign_a1_ttr.py — Amendment A1 supplement for IN-FLIGHT campaign v1.

Re-runs ONLY the strong-static arm (cheap, ~0.6 s/scenario) on the identical
campaign seeds, writing TTR_static shards to data/campaign_a1/. Also re-computes
R_static as a shard-integrity CROSS-CHECK against campaign v1 (must match ~1e-12).
Safe to run concurrently with or after campaign.py — separate shard directory.

    python scripts/campaign_a1_ttr.py --cats D1,D3,D4,D8 --n 500 --workers 12
"""
import argparse, os, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np
import pandas as pd

SEED_CAMPAIGN = 60466176
SHARD = 50
OUT = pathlib.Path("data/campaign_a1")


def run_shard(args):
    cat, lo, hi = args
    out = OUT / f"{cat}_{lo:04d}_{hi:04d}.parquet"
    if out.exists():
        return f"{cat}[{lo}:{hi}] skip"
    from rdt_core.plant_dae import PlantParams
    from rdt_core.disruptions import sample
    from rdt_core.loop import strong_params
    import importlib.util
    here = pathlib.Path(__file__).parent
    spec = importlib.util.spec_from_file_location("sp", here / "static_policy_arms.py")
    sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)
    spec3 = importlib.util.spec_from_file_location("db", here / "detection_benchmark.py")
    db = importlib.util.module_from_spec(spec3); spec3.loader.exec_module(db)

    p_slow, p_fast = PlantParams(), strong_params()
    F0 = p_slow.nominal_nut_feed()
    arms = {"slow": sp.build_arm(p_slow), "fast": sp.build_arm(p_fast)}
    x0 = db.steady_x0(p_slow, arms["slow"][0], arms["slow"][1][0], F0)
    rows, t0 = [], time.perf_counter()
    for dp in sample(cat, hi, SEED_CAMPAIGN)[lo:hi]:
        R, T = sp.run_scheduled(arms, dp, F0, x0,
                                [(0.0, "slow"), (dp.onset_hr, "fast")])
        rows.append(dict(category=cat, seed=dp.seed,
                         R_static_a1=R, TTR_static=T))
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out, index=False)
    return f"{cat}[{lo}:{hi}] done {time.perf_counter()-t0:.0f}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cats", default="D1,D3,D4,D8")
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()
    jobs = [(c, lo, min(lo + SHARD, a.n))
            for c in a.cats.split(",") for lo in range(0, a.n, SHARD)]
    if a.workers == 1:
        for j in jobs:
            print(run_shard(j), flush=True)
    else:
        from multiprocessing import Pool
        with Pool(a.workers) as pool:
            for msg in pool.imap_unordered(run_shard, jobs):
                print(msg, flush=True)


if __name__ == "__main__":
    main()
