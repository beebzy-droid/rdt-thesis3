"""scripts/gen_labels_topo.py — First TOPOLOGY-varied labels: the 2-edge solar-train
ΔG (state space changes: +5 dryer-B compartments) vs compiled null, paired on
identical scenarios. Compiler path only — legacy model is now the reference, not
the production path. Usage: python scripts/gen_labels_topo.py D3 [--append]
"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import casadi as ca

from rdt_core.plant_dae import PlantParams, wb2db
from rdt_core.disruptions import sample, dae_params
from rdt_core import icpc_graph as icpc
from rdt_core.compiler import compile_plant, apply_change, warm_start_map

DT, DAYS, R_WIN, N, SEED0 = 0.5, 30.0, 72.0, 40, 31415
SOLAR = [("V02_CRACKING", "V03B_SOLAR"), ("V03B_SOLAR", "BUF_COPRA")]


def gmax_inactive():
    G = icpc.build_g_max()
    for u, v, a in G.edges(data=True):
        if a.get("candidate"):
            G.edges[u, v]["active"] = False
    return G


def run(cpn, intg, dp, F0, x0):
    n = int(DAYS * 24 / DT)
    xk, zk = x0.copy(), np.zeros(2)
    V = np.empty(n)
    for i in range(n):
        par = dae_params(dp, i * DT, F0)[:6]
        r = intg(x0=xk, z0=zk, p=par)
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        V[i] = float(cpn.out_fn(xk, zk, par)[1])
    t = np.arange(1, n + 1) * DT
    pre = (t > dp.onset_hr - 24) & (t <= dp.onset_hr)
    win = (t > dp.onset_hr) & (t <= dp.onset_hr + R_WIN)
    return float(np.mean(V[win] / V[pre].mean()))


def main(cat, append):
    p = PlantParams(); F0 = p.nominal_nut_feed()
    c0 = compile_plant(gmax_inactive(), p)
    c1 = compile_plant(apply_change(gmax_inactive(), SOLAR), p)
    i0, i1 = (ca.integrator("P", "idas", c.dae, 0.0, DT,
                            {"abstol": 1e-8, "reltol": 1e-8}) for c in (c0, c1))
    x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                         [F0 * 0.30 * p.tau_buf * 0.8, 2000.0, 3000.0, 1000.0], [0, 0]])
    x0B = warm_start_map(x0, c0.state_names, c1.state_names,
                         {f"x_dryB_{i}": wb2db(p.x_in_wb) for i in range(5)})
    rows, t0 = [], time.perf_counter()
    for dp in sample(cat, N, SEED0):
        R0 = run(c0, i0, dp, F0, x0)
        R1 = run(c1, i1, dp, F0, x0B)
        rows.append(dict(category=cat, seed=dp.seed, unit=dp.unit,
                         severity=dp.severity, duration_hr=dp.duration_hr,
                         onset_hr=dp.onset_hr, option="solar_train",
                         R_null=R0, R_opt=R1, dR_php=R1 - R0, n_edges_changed=2,
                         data_class="SYNTHETIC/physics-forward-model"))
    df = pd.DataFrame(rows)
    out = pathlib.Path("data/labels_topo.parquet")
    if append and out.exists():
        df = pd.concat([pd.read_parquet(out), df], ignore_index=True)
    df.to_parquet(out, index=False)
    print(f"{cat}: {N}×2 runs, {time.perf_counter()-t0:.0f} s | "
          f"mean dR={df[df.category==cat].dR_php.mean():.4f} "
          f"max={df[df.category==cat].dR_php.max():.4f}")


if __name__ == "__main__":
    main(sys.argv[1], "--append" in sys.argv)
