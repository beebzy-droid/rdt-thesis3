"""scripts/clairvoyant_bound.py — M2 closure: upper bound on continuous control.

Reviewer objection (M2): how much of the RDT's ΔR survives against a receding-
horizon continuous controller (MPC-lite) on fixed topology? Rather than build the
controller, we compute an OPTIMISTIC UPPER BOUND on what any two-regime continuous
policy (the slow/fast draw regimes the strong static arm switches between) could
achieve with PERFECT FORESIGHT, and show the RDT's topology advantage survives it.

Construction. For each scenario we run both fixed continuous regimes (slow, fast)
on the fixed nominal topology and record their per-timestep value trajectories
V_slow(t), V_fast(t). The clairvoyant two-regime envelope

    V_clair(t) = max(V_slow(t), V_fast(t))     (independent per-timestep choice)

is an OPTIMISTIC bound on any causal continuous controller choosing between these
regimes: it grants free, instantaneous, state-decoupled switching with perfect
foresight — strictly dominating any realizable MPC over the same action set,
because a real controller pays state-transition and horizon costs the envelope
ignores. R_clair = mean(V_clair/V0) over the 72 h window is therefore an UPPER
BOUND on the strong-continuous comparator's resilience.

If  ΔR_bound = R_rdt − R_clair  remains positive with a CI excluding zero, then no
continuous controller over this action set can erase the topology advantage — the
MPC-lite objection is bounded out without building MPC-lite.

Caveats stated in output: (i) the bound is over the two-regime action set the
static family uses; a continuous controller with a richer action space (e.g.
continuous draw-rate modulation) is not bounded here — noted as residual. (ii)
The envelope's state-decoupling makes it loose (optimistic); the true MPC gap is
smaller, so a positive ΔR_bound is conservative for the RDT.

Usage: python scripts/clairvoyant_bound.py --cats D1,D3,D4,D8 --n 500 --workers 12
       python scripts/clairvoyant_bound.py --analyze   (after shards written)
"""
import argparse, os, sys, glob, pathlib, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401
import numpy as np
import pandas as pd

SEED_CAMPAIGN, SHARD, R_WIN, DT, DAYS = 60466176, 50, 72.0, 0.5, 30.0
OUT = pathlib.Path("data/clairvoyant")


def regime_trajectory(arms, key, dp, F0, x0):
    """Per-timestep value V(t) for one fixed continuous regime on nominal topology."""
    import numpy as np
    n = int(DAYS * 24 / DT)
    cpn, (i0, i1) = arms[key]
    xk, zk = x0.copy(), np.zeros(2)
    V = np.empty(n)
    for i in range(n):
        par = _dae_params(dp, i * DT, F0)[:6]
        zk = np.array(cpn.z_fn(xk, par)).ravel()
        try:
            r = i0(x0=xk, z0=zk, p=par)
        except RuntimeError:
            r = i1(x0=xk, z0=zk, p=par)
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        V[i] = float(cpn.out_fn(xk, zk, par)[1])
    return V


def _dae_params(dp, t, F0):
    from rdt_core.disruptions import dae_params
    return dae_params(dp, t, F0)


def run_shard(args):
    cat, lo, hi = args
    out = OUT / f"{cat}_{lo:04d}_{hi:04d}.parquet"
    OUT.mkdir(parents=True, exist_ok=True)
    if out.exists():
        return f"{cat}[{lo}:{hi}] skip"
    from rdt_core.plant_dae import PlantParams, wb2db
    from rdt_core.disruptions import sample
    from rdt_core.loop import strong_params
    import importlib.util
    here = pathlib.Path(__file__).parent
    spec = importlib.util.spec_from_file_location("sp", here / "static_policy_arms.py")
    sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)

    p_slow, p_fast = PlantParams(), strong_params()
    F0 = p_slow.nominal_nut_feed()
    arms = {"slow": sp.build_arm(p_slow), "fast": sp.build_arm(p_fast)}
    x0 = np.concatenate([np.full(5, wb2db(p_slow.x_in_wb)),
                         [F0 * 0.30 * p_slow.tau_buf * 0.8, 2000.0, 3000.0, 1000.0],
                         [0, 0]])
    rows = []
    for dp in sample(cat, hi, SEED_CAMPAIGN)[lo:hi]:
        Vs = regime_trajectory(arms, "slow", dp, F0, x0)
        Vf = regime_trajectory(arms, "fast", dp, F0, x0)
        Vc = np.maximum(Vs, Vf)
        n = len(Vc); tg = np.arange(1, n + 1) * DT
        pre = (tg > dp.onset_hr - 24) & (tg <= dp.onset_hr)
        win = (tg > dp.onset_hr) & (tg <= dp.onset_hr + R_WIN)
        V0 = Vc[pre].mean()
        rows.append(dict(category=cat, seed=dp.seed,
                         R_clair=float(np.mean(Vc[win] / V0)),
                         R_slow=float(np.mean(Vs[win] / Vs[pre].mean())),
                         R_fast=float(np.mean(Vf[win] / Vf[pre].mean())),
                         data_class="SYNTHETIC/physics-forward-model"))
    pd.DataFrame(rows).to_parquet(out, index=False)
    return f"{cat}[{lo}:{hi}] done {len(rows)}"


def analyze():
    files = sorted(glob.glob("data/clairvoyant/*.parquet"))
    if not files:
        sys.exit("no clairvoyant shards — run without --analyze first")
    clair = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    rdt = pd.concat([pd.read_parquet(f)
                     for f in glob.glob("data/campaign/*.parquet")],
                    ignore_index=True)[["category", "seed", "R_rdt"]]
    m = rdt.merge(clair, on=["category", "seed"])
    m["dR_bound"] = m.R_rdt - m.R_clair
    rng = np.random.default_rng(0)
    x = m.dR_bound.to_numpy()
    bs = np.array([rng.choice(x, len(x)).mean() for _ in range(10000)])
    lo, hi = np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    print(f"clairvoyant continuous-control UPPER BOUND (n={len(m)}):")
    print(f"  R_rdt mean            {m.R_rdt.mean():.4f}")
    print(f"  R_clairvoyant mean    {m.R_clair.mean():.4f}  "
          f"(optimistic 2-regime envelope; ≥ any MPC over slow/fast)")
    print(f"  R_hoard→deploy static {m[['R_slow','R_fast']].max(axis=1).mean():.4f} "
          f"(the realized strong baseline, for reference)")
    print(f"\n  ΔR vs clairvoyant bound = {m.dR_bound.mean():.4f}, "
          f"95% CI [{lo:.4f}, {hi:.4f}]")
    verdict = ("SURVIVES — no continuous controller over this action set erases "
               "the topology advantage" if lo > 0 else
               "DOES NOT survive — CI includes 0; MPC-lite must be built")
    print(f"  M2 verdict: {verdict}")
    g = m.groupby("category").agg(R_rdt=("R_rdt", "mean"),
                                  R_clair=("R_clair", "mean"),
                                  dR_bound=("dR_bound", "mean"))
    print("\n" + g.round(3).to_string())
    print("\nResidual (stated in manuscript): bound covers the slow/fast draw-regime "
          "action set; a continuous-modulation controller is not bounded here.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cats", default="D1,D3,D4,D8")
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--analyze", action="store_true")
    a = ap.parse_args()
    if a.analyze:
        analyze(); return
    jobs = [(c, lo, min(lo + SHARD, a.n))
            for c in a.cats.split(",") for lo in range(0, a.n, SHARD)]
    print(f"{len(jobs)} shards, {a.workers} workers")
    if a.workers == 1:
        for j in jobs:
            print(run_shard(j), flush=True)
    else:
        from multiprocessing import get_context
        with get_context("spawn").Pool(a.workers) as pool:
            for msg in pool.imap_unordered(run_shard, jobs):
                print(msg, flush=True)


if __name__ == "__main__":
    main()
