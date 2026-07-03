"""rdt_core.features — §2.1.1 feature extraction: (sim state, topology) → (X_V, X_E).

Design decision: the GAT operates on the FIXED G_max universe (29 nodes, 50 edges);
topology is encoded in the `active` edge feature, and a ΔG is a multi-hot indicator
over the candidate-edge axis. This keeps every training record the same shape
(X_V [29×12], X_E [50×8], dG [50]) — batchable without padding — while remaining
faithful to §2.1: A(t) lives in the features, not the connectivity.

Node feature schema (d_v = 12), per-channel:
  0 cap_norm        design capacity / max capacity over units (0 for non-units)
  1 load_frac       throughput / capacity at decision time (0 if unknown)
  2 health          h ∈ [0,1] for units; 1 elsewhere
  3 inv_norm        inventory / INV_SCALE for storage nodes
  4-8 kind one-hot  source | unit | storage | utility | sink
  9 is_candidate_node
  10 reserved (startup state — batch units, Phase 1)
  11 reserved (time-since-reconfig)
Edge feature schema (d_e = 8):
  0 flow_norm       modeled flow / FLOW_SCALE (0 if unmodeled)
  1 active          topology indicator A(t)
  2 candidate       reconfigurable edge flag
  3 is_utility      stream type
  4 reserved (T)  5 reserved (P)  6 reserved (capacity_util)  7 reserved (diameter)
Reserved channels are declared now so the schema is frozen before any training —
silent schema drift between dataset versions is a leakage/comparability hazard.
"""
from __future__ import annotations
import numpy as np
import networkx as nx

from . import icpc_graph as icpc

INV_SCALE = 100_000.0     # kg
FLOW_SCALE = 15_000.0     # kg/hr (≈ nominal nut feed)
CAP_NORM = {              # unit design capacities as kg/hr-equivalents [Table 5.1]
    "V01_RECEIVING": 60_000.0, "V02_CRACKING": 54_000.0, "V03_DRYING": 3_333.0,
    "V04_PRESS": 20_000.0, "V05_REFINING": 12_000.0, "V06_CARBONIZER": 333.0,
    "V07_EVAPORATOR": 5_000.0, "V03B_SOLAR": 1_667.0,
}
KINDS = ("source", "unit", "storage", "utility", "sink")
D_V, D_E = 12, 8


def universe():
    """Fixed node/edge ordering over G_max — the dataset's coordinate system."""
    G = icpc.build_g_max()
    nodes = sorted(G.nodes)
    edges = sorted(G.edges)
    return G, nodes, edges


def node_features(G, nodes, health: dict, inventories: dict, loads: dict):
    X = np.zeros((len(nodes), D_V))
    cmax = max(CAP_NORM.values())
    for i, n in enumerate(nodes):
        a = G.nodes[n]
        X[i, 0] = CAP_NORM.get(n, 0.0) / cmax
        X[i, 1] = loads.get(n, 0.0)
        X[i, 2] = health.get(n, 1.0)
        X[i, 3] = inventories.get(n, 0.0) / INV_SCALE
        X[i, 4 + KINDS.index(a["kind"])] = 1.0
        X[i, 9] = float(bool(a.get("candidate_node")))
    return X


def edge_features(G_active: nx.DiGraph, edges, flows: dict):
    X = np.zeros((len(edges), D_E))
    Gm = icpc.build_g_max()
    for j, (u, v) in enumerate(edges):
        a = Gm.edges[u, v]
        X[j, 0] = flows.get((u, v), 0.0) / FLOW_SCALE
        X[j, 1] = float(G_active.has_edge(u, v)
                        and G_active.edges[u, v].get("active", False))
        X[j, 2] = float(bool(a.get("candidate")))
        X[j, 3] = float(a.get("stream") == "utility")
    return X


def extract(cpn, G_active, xk, zk, par, nodes, edges):
    """Full snapshot → (X_V, X_E) at decision time."""
    sn = cpn.state_names
    inv = {"BUF_COPRA": xk[sn.index("I_copra")],
           "TANK_CRUDE_VCO": xk[sn.index("I_vco")],
           "YARD_SHELL": xk[sn.index("I_shell")],
           "SURGE_COCOWATER": xk[sn.index("I_ccw")]}
    health = {"V03_DRYING": par[3], "V04_PRESS": par[4], "V05_REFINING": par[5]}
    fl = dict(zip(cpn.flow_edges, np.array(cpn.flow_fn(xk, zk, par)).ravel()))
    loads = {n: fl.get(e, 0.0) / CAP_NORM[n] for n, e in
             [("V03_DRYING", ("V02_CRACKING", "V03_DRYING")),
              ("V04_PRESS", ("BUF_COPRA", "V04_PRESS")),
              ("V05_REFINING", ("TANK_CRUDE_VCO", "V05_REFINING")),
              ("V07_EVAPORATOR", ("SURGE_COCOWATER", "V07_EVAPORATOR"))]}
    Gm = icpc.build_g_max()
    return (node_features(Gm, nodes, health, inv, loads),
            edge_features(G_active, edges, fl))


def delta_multihot(edges, changed: list[tuple]) -> np.ndarray:
    v = np.zeros(len(edges))
    for e in changed:
        v[edges.index(e)] = 1.0
    return v
