"""scripts/gen_gat_dataset.py — Assemble the GAT training dataset v0.

For every labeled scenario (labels_v0 + labels_topo): rerun the compiled-null plant
to DECISION TIME (onset + 1 h detection-delay assumption [est.; BOCPD replaces this
in Phase 4]), extract the §2.1.1 feature snapshot, and attach every option row of
that scenario as one record:
    X_V [29×12], X_E [50×8], dG multi-hot [50], y = dR_php
Fixed shapes over the G_max universe → data/gat_dataset_v0.npz (+ index parquet).
Framework-agnostic arrays; PyG loader is a thin adapter (Phase 2).
"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
import casadi as ca

from rdt_core.plant_dae import PlantParams, wb2db
from rdt_core.disruptions import sample, dae_params
from rdt_core import icpc_graph as icpc
from rdt_core.compiler import compile_plant
from rdt_core import features as ft

DT = 0.5
DETECT_DELAY = 1.0   # hr [est.]
OPTION_EDGES = {
    "crude_bypass": [("TANK_CRUDE_VCO", "SNK_VCO_CRUDE")],
    "wet_route":    [("V02_CRACKING", "V04_PRESS")],
    "copra_buy":    [("SRC_COPRA_BUY", "BUF_COPRA")],
    "solar_train":  [("V02_CRACKING", "V03B_SOLAR"), ("V03B_SOLAR", "BUF_COPRA")],
}
SEED0 = 31415


def gmax_inactive():
    G = icpc.build_g_max()
    for u, v, a in G.edges(data=True):
        if a.get("candidate"):
            G.edges[u, v]["active"] = False
    return G


def main():
    lab = pd.concat([pd.read_parquet("data/labels_v0.parquet"),
                     pd.read_parquet("data/labels_topo.parquet")], ignore_index=True)
    lab["scen"] = lab.category + "_" + lab.seed.astype(str)

    p = PlantParams(); F0 = p.nominal_nut_feed()
    G0 = gmax_inactive()
    c0 = compile_plant(G0, p)
    intg = ca.integrator("P", "idas", c0.dae, 0.0, DT,
                         {"abstol": 1e-8, "reltol": 1e-8})
    x_init = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                             [F0 * 0.30 * p.tau_buf * 0.8, 2000, 3000, 1000], [0, 0]])
    _, nodes, edges = ft.universe()

    # regenerate DisruptionParams by (category, index) — seed encodes SEED0*1e5+i
    dps = {}
    for cat in lab.category.unique():
        for dp in sample(cat, 40, SEED0):
            dps[f"{cat}_{dp.seed}"] = dp

    XV, XE, DG, Y, idx = [], [], [], [], []
    t0 = time.perf_counter()
    for scen, g in lab.groupby("scen"):
        dp = dps[scen]
        n_steps = int((dp.onset_hr + DETECT_DELAY) / DT)
        xk, zk = x_init.copy(), np.zeros(2)
        for i in range(n_steps):
            par = dae_params(dp, i * DT, F0)[:6]
            r = intg(x0=xk, z0=zk, p=par)
            xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        Xv, Xe = ft.extract(c0, G0, xk, zk, par, nodes, edges)
        for _, row in g.iterrows():
            XV.append(Xv); XE.append(Xe)
            DG.append(ft.delta_multihot(edges, OPTION_EDGES[row.option]))
            Y.append(row.dR_php)
            idx.append(dict(scen=scen, category=row.category, option=row.option,
                            unit=row.unit if isinstance(row.unit, str) else "",
                            severity=row.severity, duration_hr=row.duration_hr))
    XV, XE, DG, Y = map(np.array, (XV, XE, DG, Y))
    ei = np.array([[nodes.index(u) for u, v in edges],
                   [nodes.index(v) for u, v in edges]])
    np.savez_compressed("data/gat_dataset_v0.npz", X_V=XV, X_E=XE, dG=DG, y=Y,
                        edge_index=ei, nodes=np.array(nodes), 
                        edges=np.array([f"{u}->{v}" for u, v in edges]))
    pd.DataFrame(idx).to_parquet("data/gat_dataset_v0_index.parquet", index=False)
    print(f"{len(Y)} records in {time.perf_counter()-t0:.0f} s | "
          f"X_V {XV.shape} X_E {XE.shape} dG {DG.shape} | "
          f"y: mean {Y.mean():.4f} std {Y.std():.4f} | "
          f"npz {pathlib.Path('data/gat_dataset_v0.npz').stat().st_size/1e6:.1f} MB")


if __name__ == "__main__":
    main()
