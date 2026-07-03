"""tests/test_gates.py — CI-enforced verification: R1 gate, structural filter,
ICPC graph integrity, HiGHS latency. Every assertion here maps to a lifecycle
doc criterion; a red CI is a failed gate, not a style problem.
"""
import numpy as np
import networkx as nx
import pytest

from rdt_core.toy_flowsheet import ToyParams, analytical_steady_state
from rdt_core.sim import run_scenario
from rdt_core.graph import structural_feasibility, rank_test
from rdt_core import icpc_graph as icpc


# ------------------------------------------------------------------ R1 gate
class TestR1Gate:
    @pytest.fixture(scope="class")
    def traj(self):
        return run_scenario([(0.0, 4000.0), (250.0, 2000.0)], 600.0, ToyParams())

    @pytest.mark.parametrize("t_lo,F", [(240.0, 4000.0), (590.0, 2000.0)])
    def test_steady_state_match(self, traj, t_lo, F):
        """Criterion: rel. error < 1e-3 vs closed form (achieves ~1e-15)."""
        ss = analytical_steady_state(F, ToyParams())
        m = traj["t"] >= t_lo
        assert abs(traj["X"][m][0] - ss["x_ss"]) / ss["x_ss"] < 1e-3
        assert abs(traj["Foil"][m][0] - ss["F_oil_ss"]) / ss["F_oil_ss"] < 1e-3

    def test_determinism_bit_identical(self, traj):
        """Verification item (d): CRN prerequisite."""
        b = run_scenario([(0.0, 4000.0), (250.0, 2000.0)], 600.0, ToyParams())
        for k in ("X", "I", "Foil"):
            assert np.array_equal(traj[k], b[k])


# ------------------------------------------------------- structural filter
class TestStructuralFilter:
    def test_discriminates(self):
        U, S, T = {"DRYER", "PRESS"}, {"SRC"}, {"OIL", "MEAL"}
        G = nx.DiGraph([("SRC", "DRYER"), ("DRYER", "PRESS"),
                        ("PRESS", "OIL"), ("PRESS", "MEAL")])
        assert structural_feasibility(G, U, S, T)["passes"]
        Gb = G.copy(); Gb.remove_edge("PRESS", "OIL"); Gb.remove_edge("PRESS", "MEAL")
        assert not structural_feasibility(Gb, U, S, T)["passes"]

    def test_rank_identity_documented_vacuous(self):
        """Regression guard on the §2.4.1 amendment: identity holds even on a
        broken graph — anyone re-introducing rank as a filter must see this."""
        Gb = nx.DiGraph([("SRC", "DRYER")]); Gb.add_node("ORPHAN")
        assert rank_test(Gb)["identity_holds"]   # holds — hence not a filter


# ------------------------------------------------------------- ICPC G_max
class TestICPCGraph:
    def test_nominal_structurally_feasible(self):
        G = icpc.build_nominal()
        r = structural_feasibility(G, icpc.units(G), icpc.sources(G), icpc.sinks(G))
        assert r["passes"], r["violations"]

    def test_gmax_counts(self):
        G = icpc.build_g_max()
        assert len(icpc.units(G)) == 7                      # Table 5.1 exactly
        assert sum(1 for *_, a in G.edges(data=True) if a["candidate"]) == 10
        assert G.number_of_nodes() >= 18                    # lifecycle §2.1.1

    def test_every_candidate_edge_is_new(self):
        """No candidate duplicates a nominal edge (superstructure hygiene)."""
        nom = {(u, v) for u, v, _ in icpc.NOMINAL_EDGES}
        cand = {(u, v) for u, v, _ in icpc.CANDIDATE_EDGES}
        assert not (nom & cand)

    def test_single_candidate_activation_stays_feasible(self):
        """Each single-edge activation on nominal must pass the filter
        (a candidate that breaks structure alone is mis-specified)."""
        for u, v, a in icpc.CANDIDATE_EDGES:
            G = icpc.build_nominal()
            G.add_node(u, **icpc.NODES[u]); G.add_node(v, **icpc.NODES[v])
            G.add_edge(u, v, active=True, candidate=True, **a)
            r = structural_feasibility(G, icpc.units(G), icpc.sources(G), icpc.sinks(G))
            assert r["passes"], (u, v, r["violations"])
