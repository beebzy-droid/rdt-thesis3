"""scripts/campaign.py — Full-scale paired campaign (H4/H5 final, lifecycle §5.4.3).

Per scenario, three passes:
  1) slow-regime null run collecting the 6-channel observation stream
     -> hybrid detection time t_det (BOCPD+CUSUM, locked config thr=0.85, h=12)
  2) STRONG static arm: hoard->deploy at ORACLE onset (comparator advantage kept)
  3) RDT arm: topology loop, regime switch AND decisions gated at t_det
Sharded, parallel, resumable: one parquet per (category, slice); existing shards
are skipped, so re-running the command after an interruption continues the campaign.

Run on reference hardware (12-core):
    python scripts/campaign.py --cats D1,D3,D4,D8 --n 500 --workers 12
Expected: 2,000 scenarios x ~2.2 s / worker-scenario ≈ 7 min wall at 12 workers.
Container smoke: --cats D1 --n 2 --workers 1
"""
import argparse, os, sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np
import pandas as pd

SEED_CAMPAIGN = 60466176        # fresh draw: disjoint from training 31415 AND pilot 27182
SHARD = 50                      # scenarios per shard file
OUT = pathlib.Path("data/campaign")


def run_shard(args):
    """SPAWN-SAFETY (fix 2026-07-04): Windows multiprocessing spawns workers that
    re-import this module — parent-process global mutation and env tricks do NOT
    reach them. Everything a worker needs travels in the job tuple; the output
    directory is derived HERE. Bug caught in production: --buy-cap workers wrote/
    checked the UNCAPPED directory (data protected only by the skip guard)."""
    cat, lo, hi, buy_cap = args
    out_dir = (pathlib.Path(f"data/campaign_cap{buy_cap}") if buy_cap
               else pathlib.Path("data/campaign"))
    out = out_dir / f"{cat}_{lo:04d}_{hi:04d}.parquet"
    out_dir.mkdir(parents=True, exist_ok=True)
    if out.exists():
        return f"{cat}[{lo}:{hi}] skip (exists)"
    # heavy imports inside worker (fork-safe, keeps parent light)
    import casadi as ca
    from rdt_core.plant_dae import PlantParams, wb2db
    from rdt_core.disruptions import sample, dae_params
    from rdt_core.loop import TopologyCache, run_closed_loop, strong_params
    from rdt_core.bocpd import detect
    from rdt_core.compiler import compile_plant
    from rdt_core import icpc_graph as icpc
    import importlib.util
    here = pathlib.Path(__file__).parent
    spec = importlib.util.spec_from_file_location("ce", here / "closed_loop_eval.py")
    ce = importlib.util.module_from_spec(spec); spec.loader.exec_module(ce)
    spec2 = importlib.util.spec_from_file_location("sp", here / "static_policy_arms.py")
    sp = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(sp)
    spec3 = importlib.util.spec_from_file_location("db", here / "detection_benchmark.py")
    db = importlib.util.module_from_spec(spec3); spec3.loader.exec_module(db)

    p_slow, p_fast = PlantParams(), strong_params()
    if buy_cap:
        import dataclasses
        p_slow = dataclasses.replace(p_slow, buy_cap_frac=buy_cap)
        p_fast = dataclasses.replace(p_fast, buy_cap_frac=buy_cap)
    F0 = p_slow.nominal_nut_feed()
    arms = {"slow": sp.build_arm(p_slow), "fast": sp.build_arm(p_fast)}
    cache_fast, cache_slow = TopologyCache(p_fast), TopologyCache(p_slow)
    screen = ce.get_screen()
    cpn_n, intg_n = arms["slow"][0], arms["slow"][1][0]
    x0 = db.steady_x0(p_slow, cpn_n, intg_n, F0)
    rng = np.random.default_rng(SEED_CAMPAIGN + hash(cat) % 10000)

    rows, t0 = [], time.perf_counter()
    dps = sample(cat, hi, SEED_CAMPAIGN)[lo:hi]
    for dp in dps:
        Z = db.obs_stream(dp, p_slow, cpn_n, intg_n, F0, x0, rng)
        onset_i = int(dp.onset_hr / 0.5)
        hits = [a for a in detect(Z, 0.85, cusum_h=12.0)
                if onset_i <= a <= onset_i + 96]
        delay = (hits[0] - onset_i) * 0.5 if hits else np.nan
        t_det = dp.onset_hr + (delay if np.isfinite(delay) else 1e9)
        R_st, T_st = sp.run_scheduled(arms, dp, F0, x0, [(0.0, "slow"), (dp.onset_hr, "fast")])
        R_r, T_r, sw, info = run_closed_loop(
            dp, screen, cache_fast, F0, x0,
            cache_slow=cache_slow, t_regime=t_det, t_enable=t_det)
        rows.append(dict(category=cat, seed=dp.seed, unit=dp.unit,
                         severity=dp.severity, duration_hr=dp.duration_hr,
                         onset_hr=dp.onset_hr, det_delay=delay,
                         R_static=R_st, R_rdt=R_r, dR=R_r - R_st,
                         TTR_static=T_st, TTR_rdt=T_r, n_switches=sw,
                         degraded=sum(info["degraded"]),
                         data_class="SYNTHETIC/physics-forward-model"))
    pd.DataFrame(rows).to_parquet(out, index=False)
    return f"{cat}[{lo}:{hi}] done {time.perf_counter()-t0:.0f}s"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cats", default="D1,D3,D4,D8")
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--buy-cap", type=float, default=None,
                    help="market-availability cap on purchased copra, fraction of "
                         "nominal (e.g. 0.3). Output -> data/campaign_cap{v}/")
    a = ap.parse_args()
    jobs = [(c, lo, min(lo + SHARD, a.n), a.buy_cap)
            for c in a.cats.split(",") for lo in range(0, a.n, SHARD)]
    print(f"{len(jobs)} shards x <= {SHARD} scenarios, {a.workers} workers")
    if a.workers == 1:
        for j in jobs:
            print(run_shard(j))
    else:
        # spawn on ALL platforms: matches Windows semantics, so container CI
        # exercises the same worker-isolation the production machine has
        # (fix 2026-07-04, after the fork/spawn OUT-directory bug)
        from multiprocessing import get_context
        with get_context("spawn").Pool(a.workers) as pool:
            for msg in pool.imap_unordered(run_shard, jobs):
                print(msg, flush=True)


if __name__ == "__main__":
    main()
