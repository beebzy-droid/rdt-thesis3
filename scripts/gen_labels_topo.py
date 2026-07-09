"""scripts/gen_labels_topo.py — First TOPOLOGY-varied labels: the 2-edge solar-train
ΔG (state space changes: +5 dryer-B compartments) vs compiled null, paired on
identical scenarios. Compiler path only — legacy model is now the reference, not
the production path. Usage: python scripts/gen_labels_topo.py D3 [--append]
"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np
import pandas as pd
import casadi as ca

from rdt_core.plant_dae import PlantParams, wb2db
from rdt_core.disruptions import sample, dae_params
from rdt_core import icpc_graph as icpc
from rdt_core.compiler import compile_plant, apply_change, warm_start_map

DT, DAYS, R_WIN, N, SEED0 = 0.5, 30.0, 72.0, 40, 31415
OPTIONS = {
    "solar_train": [("V02_CRACKING", "V03B_SOLAR"), ("V03B_SOLAR", "BUF_COPRA")],
    "copra_sale":  [("BUF_COPRA", "SNK_COPRA_SALE")],
    "shell_boiler": [("YARD_SHELL", "UTIL_STEAM")],
    "nut_sale":    [("V01_RECEIVING", "SNK_NUT_SALE")],
}


def gmax_inactive():
    G = icpc.build_g_max()
    for u, v, a in G.edges(data=True):
        if a.get("candidate"):
            G.edges[u, v]["active"] = False
    return G


DETECT_DELAY = 1.0  # hr [est.]


def run(arm0, arm1, dp, F0):
    """PROTOCOL FIX 2026-07-03 (Eq. 2.2 semantics): ΔG is applied AT DECISION TIME
    (onset + detect delay) via warm-start state remap — not from t=0. Always-on
    activation contaminated the per-arm baseline V0 for options with nonzero
    nominal value flow (exposed by shell_boiler on D1). arm=(cpn, intg, x0, names);
    arm1=None runs the null arm end-to-end."""
    c0, i0, x0, n0 = arm0
    n = int(DAYS * 24 / DT)
    k_sw = n if arm1 is None else int((dp.onset_hr + DETECT_DELAY) / DT)
    xk, zk = x0.copy(), np.zeros(2)
    V = np.empty(n)
    cpn, intg = c0, i0
    for i in range(n):
        if i == k_sw:
            c1, i1, x1_init, n1 = arm1
            xk = warm_start_map(xk, n0, n1,
                                {nm: x1_init[j] for j, nm in enumerate(n1)})
            cpn, intg = c1, i1
        par = dae_params(dp, i * DT, F0)[:6]
        r = intg(x0=xk, z0=zk, p=par)
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        V[i] = float(cpn.out_fn(xk, zk, par)[1])
    t = np.arange(1, n + 1) * DT
    pre = (t > dp.onset_hr - 24) & (t <= dp.onset_hr)
    win = (t > dp.onset_hr) & (t <= dp.onset_hr + R_WIN)
    return float(np.mean(V[win] / V[pre].mean()))


def main(cat, append, opts):
    p = PlantParams(); F0 = p.nominal_nut_feed()
    c0 = compile_plant(gmax_inactive(), p)
    mk = lambda c: ca.integrator("P", "idas", c.dae, 0.0, DT,
                                 {"abstol": 1e-8, "reltol": 1e-8})
    i0 = mk(c0)
    x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                         [F0 * 0.30 * p.tau_buf * 0.8, 2000.0, 3000.0, 1000.0], [0, 0]])
    arms = {}
    for name in opts:
        c1 = compile_plant(apply_change(gmax_inactive(), OPTIONS[name]), p)
        x1 = warm_start_map(x0, c0.state_names, c1.state_names,
                            {f"x_dryB_{i}": wb2db(p.x_in_wb) for i in range(5)})
        arms[name] = (c1, mk(c1), x1, c1.state_names)
    arm0 = (c0, i0, x0, c0.state_names)
    rows, t0 = [], time.perf_counter()
    for dp in sample(cat, N, SEED0):
        R0 = run(arm0, None, dp, F0)
        for name, arm1 in arms.items():
            R1 = run(arm0, arm1, dp, F0)
            rows.append(dict(category=cat, seed=dp.seed, unit=dp.unit,
                             severity=dp.severity, duration_hr=dp.duration_hr,
                             onset_hr=dp.onset_hr, option=name,
                             R_null=R0, R_opt=R1, dR_php=R1 - R0,
                             n_edges_changed=len(OPTIONS[name]),
                             data_class="SYNTHETIC/physics-forward-model"))
    df = pd.DataFrame(rows)
    out = pathlib.Path("data/labels_topo.parquet")
    if append and out.exists():
        df = pd.concat([pd.read_parquet(out), df], ignore_index=True)
    df.to_parquet(out, index=False)
    m = df[df.category == cat].groupby("option").dR_php.agg(["mean", "max"]).round(4)
    print(f"{cat}: {time.perf_counter()-t0:.0f} s\n{m.to_string()}")


if __name__ == "__main__":
    opts = [a for a in sys.argv[2:] if not a.startswith("--")] or list(OPTIONS)
    main(sys.argv[1], "--append" in sys.argv, opts)
