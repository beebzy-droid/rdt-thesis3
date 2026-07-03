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
@pytest.fixture(scope="module")
def traj():
    return run_scenario([(0.0, 4000.0), (250.0, 2000.0)], 600.0, ToyParams())


class TestR1Gate:

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
        assert len(icpc.units(G)) == 7                      # Table 5.1 core exactly
        n_cand = sum(1 for *_, a in G.edges(data=True) if a["candidate"])
        assert n_cand == 19
        assert 45 <= G.number_of_edges() <= 60              # lifecycle §2.1.2 band
        assert G.number_of_nodes() >= 18

    def test_every_candidate_edge_is_new(self):
        """No candidate duplicates a nominal edge (superstructure hygiene)."""
        nom = {(u, v) for u, v, _ in icpc.NOMINAL_EDGES}
        cand = {(u, v) for u, v, _ in icpc.CANDIDATE_EDGES}
        assert not (nom & cand)

    def test_each_option_activation_stays_feasible(self):
        """Every ΔG activation unit (single edge, or full OPTION_GROUP) applied
        to nominal must pass the filter — a mis-specified option fails here."""
        grouped = {e for edges in icpc.OPTION_GROUPS.values() for e in edges}
        singles = [[(u, v, a)] for u, v, a in icpc.CANDIDATE_EDGES
                   if (u, v) not in grouped]
        groups = [[(u, v, dict(icpc.build_g_max().edges[u, v]))
                   for u, v in edges] for edges in icpc.OPTION_GROUPS.values()]
        for change in singles + groups:
            G = icpc.build_nominal()
            for u, v, a in change:
                for n in (u, v):
                    if n not in G:
                        G.add_node(n, **icpc.NODES[n])
                G.add_edge(u, v, **{**a, "active": True})
            r = structural_feasibility(G, icpc.units(G), icpc.sources(G), icpc.sinks(G))
            assert r["passes"], (change, r["violations"])

    def test_partial_group_activation_is_infeasible(self):
        """Activating only half the solar-train group must FAIL the filter —
        this is the property that makes option groups the ΔG unit."""
        G = icpc.build_nominal()
        G.add_node("V03B_SOLAR", **icpc.NODES["V03B_SOLAR"])
        G.add_edge("V02_CRACKING", "V03B_SOLAR", active=True)
        r = structural_feasibility(G, icpc.units(G) | {"V03B_SOLAR"},
                                   icpc.sources(G), icpc.sinks(G))
        assert not r["passes"]


class TestPlantDAE:
    """Weeks 8–18 exit criteria (lifecycle §5.1.2 verification (b), (e))."""
    def test_thirty_day_gates(self):
        from rdt_core.plant_dae import run_nominal
        r = run_nominal(30.0)
        assert r["closure"] < 0.005, f"closure {r['closure']:.4%}"      # gate (b)
        assert r["wall_s"] < 60.0, f"wall {r['wall_s']:.1f}s"           # gate (e)
        assert abs(r["x_out_wb"] - 0.06) < 0.003                        # Table 5.1


class TestDisruptions:
    """D1–D8 sampler and profile properties (lifecycle Table 5.2)."""
    def test_sampler_deterministic(self):
        from rdt_core.disruptions import sample
        a, b = sample("D1", 20, 7), sample("D1", 20, 7)
        assert all(x == y for x, y in zip(a, b))          # CRN prerequisite

    def test_feed_profile_envelope(self):
        from rdt_core.disruptions import sample, feed_multiplier
        for dp in sample("D1", 10, 3):
            t_hold = dp.onset_hr + dp.ramp_hr + dp.duration_hr / 2
            assert abs(feed_multiplier(dp, dp.onset_hr - 1) - 1.0) < 1e-12
            assert abs(feed_multiplier(dp, t_hold) - (1 - dp.severity)) < 1e-9
            t_far = dp.onset_hr + dp.ramp_hr + dp.duration_hr + 10 * dp.recovery_tau_hr
            assert feed_multiplier(dp, t_far) > 1 - dp.severity * 1e-4

    def test_unmapped_categories_refuse(self):
        """D5/D6 still require the full topology-DAE; D3/D4 mapped 2026-07-03."""
        import pytest as _pt
        from rdt_core.disruptions import sample, dae_params
        with _pt.raises(NotImplementedError):
            dae_params(sample("D5", 1, 1)[0], 100.0, 12000.0)

    def test_d3_outage_maps_to_health(self):
        from rdt_core.disruptions import sample, dae_params
        dp = sample("D3", 3, 2)[0]
        pin = dae_params(dp, dp.onset_hr + 1.0, 12000.0)
        pout = dae_params(dp, dp.onset_hr + dp.duration_hr + 1.0, 12000.0)
        assert min(pin[3:6]) == 0.0 and min(pout[3:6]) == 1.0
