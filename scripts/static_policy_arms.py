"""scripts/static_policy_arms.py — Onset-scheduled static comparator arms.

Two additional fixed-topology policies per scenario, switching draw regime at the
EXACT disruption onset (oracle information granted to the static side; RDT keeps
its 1 h detection delay — comparison is conservative by construction):
    hoard_deploy : slow draws -> fast draws at onset   (bridge-stock then burn)
    deploy_hoard : fast draws -> slow draws at onset
Combined with the existing passive (slow) and aggressive (fast) arms this gives a
4-policy family; the per-scenario max is the bracketing static comparator.
Usage: python scripts/static_policy_arms.py <cat> [SLICE via env]
"""
import sys, os, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np
import pandas as pd
import casadi as ca

from rdt_core.plant_dae import PlantParams, wb2db
from rdt_core.disruptions import sample, dae_params
from rdt_core.compiler import compile_plant
from rdt_core.loop import strong_params
from rdt_core import icpc_graph as icpc

DT, DAYS, R_WIN = 0.5, 30.0, 72.0
SEED_EVAL, N_EVAL = 27182, 40


def nominal_inactive():
    G = icpc.build_g_max()
    for u, v, a in G.edges(data=True):
        if a.get("candidate"):
            G.edges[u, v]["active"] = False
    return G


def build_arm(p):
    c = compile_plant(nominal_inactive(), p)
    intg = ca.integrator("P", "idas", c.dae, 0.0, DT,
                         {"abstol": 1e-8, "reltol": 1e-8})
    i_loose = ca.integrator("PL", "idas", c.dae, 0.0, DT,
                            {"abstol": 1e-6, "reltol": 1e-6})
    return c, (intg, i_loose)


def run_scheduled(arms, dp, F0, x0, schedule):
    """schedule: list of (t_from_hr, arm_key). arms: {'slow','fast'} -> (cpn, intgs)."""
    n = int(DAYS * 24 / DT)
    xk, zk = x0.copy(), np.zeros(2)
    V = np.empty(n)
    for i in range(n):
        t = i * DT
        key = max((s for s in schedule if s[0] <= t), key=lambda s: s[0])[1]
        cpn, (i0, i1) = arms[key]
        par = dae_params(dp, t, F0)[:6]
        zk = np.array(cpn.z_fn(xk, par)).ravel()
        try:
            r = i0(x0=xk, z0=zk, p=par)
        except RuntimeError:
            r = i1(x0=xk, z0=zk, p=par)
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        V[i] = float(cpn.out_fn(xk, zk, par)[1])
    tg = np.arange(1, n + 1) * DT
    pre = (tg > dp.onset_hr - 24) & (tg <= dp.onset_hr)
    win = (tg > dp.onset_hr) & (tg <= dp.onset_hr + R_WIN)
    V0 = V[pre].mean()
    R = float(np.mean(V[win] / V0))
    # TTR80, corrected semantics (Amendment A1, 2026-07-03)
    ratio = V / V0
    post = np.where(tg > dp.onset_hr)[0]
    k6 = int(6 / DT)
    below = post[ratio[post] < 0.8]
    if below.size == 0:
        ttr = 0.0
    else:
        ttr = np.nan
        for j in post[post >= below[0]]:
            if j + k6 <= n and np.all(ratio[j:j + k6] >= 0.8):
                ttr = tg[j] - dp.onset_hr
                break
    return R, ttr


def main(cat):
    p_slow = PlantParams()
    p_fast = strong_params()
    F0 = p_slow.nominal_nut_feed()
    arms = {"slow": build_arm(p_slow), "fast": build_arm(p_fast)}
    x0 = np.concatenate([np.full(5, wb2db(p_slow.x_in_wb)),
                         [F0 * 0.30 * p_slow.tau_buf * 0.8, 2000.0, 3000.0, 1000.0],
                         [0, 0]])
    dps = sample(cat, N_EVAL, SEED_EVAL)
    sl = os.environ.get("SLICE", "")
    if sl:
        a, b = map(int, sl.split(":")); dps = dps[a:b]
    rows, t0 = [], time.perf_counter()
    for dp in dps:
        R_hd, T_hd = run_scheduled(arms, dp, F0, x0,
                                   [(0.0, "slow"), (dp.onset_hr, "fast")])
        R_dh, _ = run_scheduled(arms, dp, F0, x0,
                                [(0.0, "fast"), (dp.onset_hr, "slow")])
        rows.append(dict(category=cat, seed=dp.seed,
                         R_hoard_deploy=R_hd, TTR_hoard_deploy=T_hd,
                         R_deploy_hoard=R_dh,
                         data_class="SYNTHETIC/physics-forward-model"))
    df = pd.DataFrame(rows)
    out = pathlib.Path("data/static_policy_arms.parquet")
    if out.exists():
        df = pd.concat([pd.read_parquet(out), df], ignore_index=True)
    df.to_parquet(out, index=False)
    g = df[df.category == cat]
    print(f"{cat}: {len(g)} scen, {time.perf_counter()-t0:.0f} s | "
          f"hoard→deploy mean R={g.R_hoard_deploy.mean():.3f} | "
          f"deploy→hoard mean R={g.R_deploy_hoard.mean():.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
