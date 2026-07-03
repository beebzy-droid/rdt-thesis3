"""rdt_core.graph — Process graph object and structural feasibility (Eq. 2.11).

The graph is the runtime data structure the whole RDT is built on:
topology is a state variable, not compile-time code (lifecycle doc §3.1.3).
"""
from __future__ import annotations
import networkx as nx
import numpy as np


def incidence_matrix(G: nx.DiGraph) -> tuple[np.ndarray, list, list]:
    """Node-arc incidence matrix S: S[i,e] = -1 if edge e leaves node i, +1 if enters.

    Rows = balance equations per node; columns = stream flows F.
    S @ F = b is the steady-state total-mass balance (Eq. 2.10).
    """
    nodes = list(G.nodes)
    edges = list(G.edges)
    S = np.zeros((len(nodes), len(edges)))
    idx = {n: i for i, n in enumerate(nodes)}
    for e, (u, v) in enumerate(edges):
        S[idx[u], e] = -1.0
        S[idx[v], e] = +1.0
    return S, nodes, edges


def rank_test(G: nx.DiGraph) -> dict:
    """Incidence rank identity — retained as a CONSISTENCY check only.

    AMENDMENT FINDING (week 0, toy gate): rank(S) = |V| − n_cc holds identically
    for ANY graph's total-mass incidence matrix, so Eq. 2.11 alone has zero
    discriminating power on total mass. It becomes non-vacuous only on the
    component-stacked S (oil/water/solids with yield coefficients) — Phase 1
    deliverable. Lifecycle doc §2.4.1 to be amended accordingly.
    """
    S, nodes, edges = incidence_matrix(G)
    r = int(np.linalg.matrix_rank(S)) if edges else 0
    n_cc = nx.number_weakly_connected_components(G)
    return {"rank": r, "required": len(nodes) - n_cc, "identity_holds": r == len(nodes) - n_cc}


def structural_feasibility(G: nx.DiGraph, units: set, sources: set, sinks: set) -> dict:
    """The operational microsecond-cost hard filter (replaces naive Eq. 2.11 use).

    A reconfigured topology G' is structurally feasible iff:
      (a) every process unit has in-degree ≥ 1 AND out-degree ≥ 1
          (no starved inlets, no stranded outlets);
      (b) every unit lies on some source→sink directed path
          (material can actually transit it);
      (c) at least one source reaches at least one sink.
    Checks (a)–(c) are O(|V| + |E|) via BFS — cheaper than the rank computation
    they replace, and actually discriminating.
    """
    fails = []
    for u in units:
        if u not in G or G.in_degree(u) == 0 or G.out_degree(u) == 0:
            fails.append(f"unit {u}: in={G.in_degree(u) if u in G else 0}, "
                         f"out={G.out_degree(u) if u in G else 0}")
    reach_fwd = set().union(*[nx.descendants(G, s) | {s} for s in sources if s in G]) if sources else set()
    reach_bwd = set().union(*[nx.ancestors(G, t) | {t} for t in sinks if t in G]) if sinks else set()
    on_path = reach_fwd & reach_bwd
    for u in units:
        if u not in on_path:
            fails.append(f"unit {u}: not on any source→sink path")
    if not (reach_fwd & sinks):
        fails.append("no source reaches any sink")
    return {"passes": len(fails) == 0, "violations": fails}
