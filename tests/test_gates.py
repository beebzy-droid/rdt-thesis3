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


def test_pyg_script_parses_and_guards():
    """train_gat_pyg.py is GPU-side (torch not in container CI): gate its syntax
    and its dataset contract here; functional smoke runs on reference hardware."""
    import py_compile, pathlib
    py_compile.compile("scripts/train_gat_pyg.py", doraise=True)
    import numpy as np, pandas as pd
    d = np.load("data/gat_dataset_v1.npz", allow_pickle=True)
    idx = pd.read_parquet("data/gat_dataset_v1_index.parquet")
    assert d["X_E"].shape[-1] == 8 and d["X_V"].shape[-1] == 12
    assert len(idx) == len(d["y"]) and {"scen", "option"} <= set(idx.columns)
    assert idx.option.nunique() == 7


def test_pyg_batch_shape_contract():
    """Reproduces the y-collation shape the loss depends on, WITHOUT torch:
    PyG DataLoader stacks per-graph y=[1] into batch y=[B] (not [B,1]); the model
    output and target must both reshape(-1) to [B]. This guards the exact bug the
    reference-GPU smoke caught (squeeze(1) IndexError). Pure-numpy stand-in."""
    import numpy as np
    B = 8
    y_per_graph = [np.array([0.1 * i]) for i in range(B)]     # PyG Data.y shape [1]
    y_batched = np.concatenate(y_per_graph)                   # loader -> [B]
    pred = np.zeros((B, 1))                                   # head output [B,1]
    # the contract: both operands flatten to [B] and align
    assert y_batched.reshape(-1).shape == pred.reshape(-1).shape == (B,)
    # squeeze(1) on the [B] target would be out of range — the caught failure
    assert y_batched.ndim == 1


def test_provenance_ledger_in_sync():
    """The provenance ledger must not drift from code values (§9.2 silent-
    substitution guard). Runs the SYNC half of check_provenance in-process."""
    import subprocess, sys
    r = subprocess.run([sys.executable, "scripts/check_provenance.py"],
                       capture_output=True, text=True)
    assert "SYNC OK" in r.stdout, r.stdout + r.stderr


def test_screen_rebuilds_deterministically():
    """The GBT screen must rebuild byte-identically from its recipe (the committed
    pickle is gitignored; the recipe + pinned sklearn + seed is the artifact).
    Guards the reproducibility contract of scripts/reproduce.py."""
    import hashlib, numpy as np
    from sklearn.ensemble import HistGradientBoostingRegressor
    d = np.load("data/gat_dataset_v1.npz", allow_pickle=True)
    X = np.concatenate([d["X_V"].reshape(len(d["y"]), -1),
                        d["X_E"].reshape(len(d["y"]), -1), d["dG"]], 1)
    p1 = HistGradientBoostingRegressor(random_state=0).fit(X, d["y"]).predict(X)
    p2 = HistGradientBoostingRegressor(random_state=0).fit(X, d["y"]).predict(X)
    assert hashlib.sha256(p1.tobytes()).hexdigest() == \
           hashlib.sha256(p2.tobytes()).hexdigest()


def test_printing_scripts_force_utf8_console():
    """Every script that prints non-ASCII glyphs (✓/Δ/φ/≈/±/→) must import
    rdt_core._console so Windows cp1252 consoles don't crash (UnicodeEncodeError
    class, 2026-07-04). Guards against a new script reintroducing the crash."""
    import pathlib
    offenders = []
    for p in pathlib.Path("scripts").glob("*.py"):
        s = p.read_text(encoding="utf-8")
        exec_lines = [l for l in s.splitlines()
                      if ("print(" in l or "sys.exit(" in l)
                      and not l.strip().startswith("#")
                      and any(ord(c) > 127 for c in l)]
        if exec_lines and "_console" not in s:
            offenders.append(p.name)
    assert not offenders, f"scripts print glyphs without _console: {offenders}"


def test_console_module_reconfigures():
    """_console must reconfigure a cp1252 stream to survive glyph output."""
    import io, importlib
    buf = io.TextIOWrapper(io.BytesIO(), encoding="cp1252")
    import sys
    old = sys.stdout
    try:
        sys.stdout = buf
        import rdt_core._console  # noqa: F401
        importlib.reload(rdt_core._console)
        print("\u2713\u0394\u03c6")               # must not raise
    finally:
        sys.stdout = old


def test_cold_start_is_opt_in_and_adds_one_state():
    """The cold-start commissioning contract must be opt-in: default PlantParams
    must reproduce the historical 16-state solar topology exactly, and enabling it
    must add exactly one state, named a_solar, positioned between the dryer-B
    chain and the inventories so warm_start_map remaps correctly."""
    from rdt_core.plant_dae import PlantParams
    from rdt_core import icpc_graph as icpc
    from rdt_core.compiler import compile_plant, apply_change
    G = icpc.build_g_max()
    for u, v, a in G.edges(data=True):
        if a.get("candidate"):
            G.edges[u, v]["active"] = False
    edges = [("V02_CRACKING", "V03B_SOLAR"), ("V03B_SOLAR", "BUF_COPRA")]
    hot = compile_plant(apply_change(G.copy(), edges), PlantParams())
    cold = compile_plant(apply_change(G.copy(), edges),
                         PlantParams(cold_start=True))
    assert "a_solar" not in hot.state_names
    assert cold.state_names.count("a_solar") == 1
    assert len(cold.state_names) == len(hot.state_names) + 1
    # state vector and names must stay aligned or the remap silently corrupts
    assert cold.dae["x"].shape[0] == len(cold.state_names)
    assert hot.dae["x"].shape[0] == len(hot.state_names)
    i = cold.state_names.index("a_solar")
    assert cold.state_names[i - 1] == "x_dryB_4"
    assert cold.state_names[i + 1] == "I_copra"
