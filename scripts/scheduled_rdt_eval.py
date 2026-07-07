"""scripts/scheduled_rdt_eval.py — Symmetric-arm evaluation (§5.4.2 fix).

RDT topology loop riding the WINNING continuous policy (hoard→deploy), regime
switch at onset + 1 h (RDT's own detection assumption — NOT the oracle onset the
static arms receive). Comparators, in decreasing strictness:
  best-of-4 hindsight static  (per-scenario max — stronger than any causal policy)
  hoard→deploy static         (single causal rule, oracle onset — the §5.4.2 strong baseline)
Usage: python scripts/scheduled_rdt_eval.py <cat>   [SLICE env]
"""
import sys, os, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd

from rdt_core.plant_dae import PlantParams, wb2db
from rdt_core.disruptions import sample
from rdt_core.loop import TopologyCache, run_closed_loop, strong_params
import importlib.util
spec = importlib.util.spec_from_file_location(
    "ce", pathlib.Path(__file__).parent / "closed_loop_eval.py")
ce = importlib.util.module_from_spec(spec); spec.loader.exec_module(ce)

SEED_EVAL, N_EVAL, DETECT = 27182, 40, 1.0


def main(cat):
    p_slow, p_fast = PlantParams(), strong_params()
    F0 = p_slow.nominal_nut_feed()
    cache_fast = TopologyCache(p_fast)
    cache_slow = TopologyCache(p_slow)
    screen = ce.get_screen()
    x0 = np.concatenate([np.full(5, wb2db(p_slow.x_in_wb)),
                         [F0 * 0.30 * p_slow.tau_buf * 0.8, 2000.0, 3000.0, 1000.0],
                         [0, 0]])
    dps = sample(cat, N_EVAL, SEED_EVAL)
    sl = os.environ.get("SLICE", "")
    if sl:
        a, b = map(int, sl.split(":")); dps = dps[a:b]
    rows, t0 = [], time.perf_counter()
    for dp in dps:
        R, T, sw, info = run_closed_loop(
            dp, screen, cache_fast, F0, x0,
            cache_slow=cache_slow, t_regime=dp.onset_hr + DETECT)
        rows.append(dict(category=cat, seed=dp.seed, R_rdt_sched=R,
                         TTR_rdt_sched=T, n_switches=sw,
                         degraded=sum(info["degraded"]),
                         data_class="SYNTHETIC/physics-forward-model"))
    df = pd.DataFrame(rows)
    out = pathlib.Path("data/rdt_scheduled.parquet")
    if out.exists():
        df = pd.concat([pd.read_parquet(out), df], ignore_index=True)
    df.to_parquet(out, index=False)
    g = df[df.category == cat]
    print(f"{cat}: {len(g)} scen, {time.perf_counter()-t0:.0f} s | "
          f"R_rdt_sched mean={g.R_rdt_sched.mean():.3f} | sw med={g.n_switches.median():.0f}")


if __name__ == "__main__":
    main(sys.argv[1])
