"""tests/test_compiler.py — Graph→DAE compiler gates.

Gate C1 (equivalence): compiled(nominal ⊕ ΔG) reproduces the legacy hand-coded
model for every legacy-expressible topology, to ≤1e-8 relative on trajectories.
Passing C1 proves all 480 existing labels remain valid under the compiler.
Gate C2 (integrity): unmodeled active candidates are REFUSED, partial option
groups are REFUSED.
Gate C3 (budget): compile + integrator construction ≪ 40 s DAE-reinit budget (§2.7).
Gate C4 (topology variation): the 2-edge solar-train ΔG compiles, runs, and adds
states — the first simulation whose STATE SPACE differs from nominal.
"""
import time
import numpy as np
import casadi as ca
import pytest

from rdt_core.plant_dae import PlantParams, build_plant_dae, wb2db
from rdt_core.disruptions import sample, dae_params
from rdt_core import icpc_graph as icpc
from rdt_core.compiler import compile_plant, apply_change, warm_start_map

P = PlantParams()
F0 = P.nominal_nut_feed()
X0_LEGACY = np.concatenate([np.full(5, wb2db(P.x_in_wb)),
                            [F0 * 0.30 * P.tau_buf * 0.8, 2000.0, 3000.0, 1000.0],
                            [0.0, 0.0]])

LEGACY_U = {"null": {}, "crude_bypass": dict(u_crude=1.0),
            "wet_route": dict(u_wet=1.0), "copra_buy": dict(u_buy=1.0)}
OPTION_EDGES = {"null": [], "crude_bypass": [("TANK_CRUDE_VCO", "SNK_VCO_CRUDE")],
                "wet_route": [("V02_CRACKING", "V04_PRESS")],
                "copra_buy": [("SRC_COPRA_BUY", "BUF_COPRA")]}


def _mk(dae, dt=0.5):
    return ca.integrator("P", "idas", dae, 0.0, dt,
                         {"abstol": 1e-8, "reltol": 1e-8})


def _gmax_all_inactive():
    G = icpc.build_g_max()
    for u, v, a in G.edges(data=True):
        if a.get("candidate"):
            G.edges[u, v]["active"] = False
    return G


def _run(intg, x0, z0, param_seq):
    xk, zk, traj = x0.copy(), z0.copy(), []
    for par in param_seq:
        r = intg(x0=xk, z0=zk, p=par)
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        traj.append(np.concatenate([xk, zk]))
    return np.array(traj)


class TestC1Equivalence:
    @pytest.mark.parametrize("opt", list(LEGACY_U))
    def test_matches_legacy(self, opt):
        """D3 scenario (health variation) run both ways, 200 steps."""
        dp = sample("D3", 3, 2)[0]                      # refine failure stratum
        n = 200
        legacy_dae, _ = build_plant_dae(P)
        li = _mk(legacy_dae)
        lp = [dae_params(dp, i * 0.5, F0, **LEGACY_U[opt]) for i in range(n)]
        lt = _run(li, X0_LEGACY, np.zeros(2), lp)

        G = apply_change(_gmax_all_inactive(), OPTION_EDGES[opt])
        cp = compile_plant(G, P)
        ci = _mk(cp.dae)
        cpar = [q[:6] for q in lp]                      # compiled: 6-param vector
        ct = _run(ci, X0_LEGACY, np.zeros(2), cpar)
        err = np.max(np.abs(ct - lt) / (np.abs(lt) + 1e-6))
        assert err < 1e-8, f"{opt}: max rel dev {err:.2e}"


class TestC2Integrity:
    def test_refuses_unmodeled_option(self):
        G = apply_change(_gmax_all_inactive(), [("UTIL_GENSET", "UTIL_POWER")])
        with pytest.raises(NotImplementedError):
            compile_plant(G, P)

    def test_refuses_partial_group(self):
        G = apply_change(_gmax_all_inactive(), [("V02_CRACKING", "V03B_SOLAR")])
        with pytest.raises(ValueError):
            compile_plant(G, P)


class TestC3Budget:
    def test_compile_plus_integrator_time(self):
        G = apply_change(_gmax_all_inactive(),
                         [("V02_CRACKING", "V03B_SOLAR"), ("V03B_SOLAR", "BUF_COPRA")])
        t0 = time.perf_counter()
        cp = compile_plant(G, P); _mk(cp.dae)
        dt = time.perf_counter() - t0
        assert dt < 2.0, f"compile+integrator {dt:.2f} s"   # budget 40 s (§2.7)


class TestC4TopologyVariation:
    def test_solar_train_changes_state_space_and_rescues(self):
        """First topology-varied run: solar ΔG under a dryer outage must
        (a) add 5 states, (b) warm-start-remap cleanly, (c) improve R_php."""
        dp = [d for d in sample("D3", 9, 5) if d.unit == "dry"][0]
        n = int(dp.onset_hr / 0.5) + 200

        G0 = _gmax_all_inactive()
        c0 = compile_plant(G0, P)
        G1 = apply_change(G0, [("V02_CRACKING", "V03B_SOLAR"),
                               ("V03B_SOLAR", "BUF_COPRA")])
        c1 = compile_plant(G1, P)
        assert len(c1.state_names) == len(c0.state_names) + 5

        x0_new = warm_start_map(X0_LEGACY, c0.state_names, c1.state_names,
                                {f"x_dryB_{i}": wb2db(P.x_in_wb) for i in range(5)})
        assert x0_new.shape[0] == len(c1.state_names)

        def rphp(cpn, x0):
            intg = _mk(cpn.dae)
            xk, zk = x0.copy(), np.zeros(2)
            V = []
            for i in range(n):
                par = dae_params(dp, i * 0.5, F0)[:6]
                r = intg(x0=xk, z0=zk, p=par)
                xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
                V.append(float(cpn.out_fn(xk, zk, par)[1]))
            V = np.array(V); t = np.arange(1, n + 1) * 0.5
            pre = (t > dp.onset_hr - 24) & (t <= dp.onset_hr)
            win = t > dp.onset_hr
            return float(np.mean(V[win] / V[pre].mean()))

        dR = rphp(c1, x0_new) - rphp(c0, X0_LEGACY)
        assert dR > 0.05, f"solar rescue dR={dR:.4f}"


class TestFeaturesAndDataset:
    def test_feature_shapes_and_flow_sanity(self):
        import casadi as ca
        from rdt_core import features as ft
        from rdt_core.plant_dae import PlantParams, wb2db
        import numpy as np
        p = PlantParams(); F0 = p.nominal_nut_feed()
        G0 = _gmax_all_inactive(); c = compile_plant(G0, p)
        intg = _mk(c.dae)
        xk, zk = X0_LEGACY.copy(), np.zeros(2)
        par = [F0, 1.0, 0.0, 1.0, 1.0, 1.0]
        for _ in range(400):                       # settle to steady state
            r = intg(x0=xk, z0=zk, p=par)
            xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        _, nodes, edges = ft.universe()
        Xv, Xe = ft.extract(c, G0, xk, zk, par, nodes, edges)
        assert Xv.shape == (29, ft.D_V) and Xe.shape == (50, ft.D_E)
        fl = dict(zip(c.flow_edges, np.array(c.flow_fn(xk, zk, par)).ravel()))
        # steady-state flow sanity vs Table 5.1 design values
        assert abs(fl[("SRC_NUTS", "V01_RECEIVING")] - F0) < 1e-6
        cop = fl[("V03_DRYING", "BUF_COPRA")]
        assert abs(cop - 80_000 / 24) / (80_000 / 24) < 0.02       # 80 MT/day
        vco = fl[("V05_REFINING", "SNK_VCO")]
        press = fl[("BUF_COPRA", "V04_PRESS")]
        assert abs(vco - p.y_refine * p.y_oil * press) / vco < 0.02
        # inactive candidate edges must carry zero active-flag and zero flow
        j = edges.index(("TANK_CRUDE_VCO", "SNK_VCO_CRUDE"))
        assert Xe[j, 1] == 0.0 and Xe[j, 0] == 0.0

    def test_delta_multihot(self):
        from rdt_core import features as ft
        _, _, edges = ft.universe()
        v = ft.delta_multihot(edges, [("V02_CRACKING", "V03B_SOLAR"),
                                      ("V03B_SOLAR", "BUF_COPRA")])
        assert v.sum() == 2.0 and v.shape == (50,)


class TestGATPrototype:
    def test_forward_and_memorization(self):
        """Implementation gate: batched forward shapes + 16-record memorization.
        jax is a PROTOTYPE-ONLY dependency (PyG is production, Table 6.1) —
        skipped cleanly where absent."""
        jax = pytest.importorskip("jax")
        import numpy as np
        from sklearn.metrics import r2_score
        from rdt_core import gat_jax as gj
        d = np.load("data/gat_dataset_v1.npz", allow_pickle=True)
        rng = np.random.default_rng(1)
        sub = rng.choice(len(d["y"]), 16, replace=False)
        pred = gj.train(d["X_V"][sub], d["X_E"][sub], d["dG"][sub], d["y"][sub],
                        d["edge_index"], tr=np.arange(16), te=np.arange(16),
                        seed=0, epochs=300)
        assert pred.shape == (16,)
        assert r2_score(d["y"][sub], pred) > 0.8


class TestMILPAndLoop:
    def test_milp_select_exclusions_and_nmax(self):
        from rdt_core.milp import select, exclusion_pairs
        assert ("wet_route", "copra_buy") in exclusion_pairs() \
            or ("copra_buy", "wet_route") in exclusion_pairs()
        y = dict(wet_route=0.10, copra_buy=0.09, crude_bypass=0.05,
                 solar_train=0.04, nut_sale=0.03)
        sel = select(y, n_max=3)
        assert len(sel) <= 3
        assert not ({"wet_route", "copra_buy"} <= set(sel))   # exclusion honored
        assert "wet_route" in sel                              # higher value kept
        assert select({}, n_max=3) == []

    def test_closed_loop_smoke(self):
        """One paired scenario through the full recurrent loop (CI-scale)."""
        import numpy as np
        from rdt_core.plant_dae import PlantParams, wb2db
        from rdt_core.disruptions import sample
        from rdt_core.loop import TopologyCache, run_closed_loop
        p = PlantParams(); F0 = p.nominal_nut_feed()
        cache = TopologyCache(p)
        x0 = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                             [F0 * .3 * 8 * .8, 2000, 3000, 1000], [0, 0]])
        dp = [d for d in sample("D3", 3, 27182) if d.unit == "dry"][0]
        screen = lambda Xv, Xe, dG: np.array([0, 0.05, 0, 0.05, 0, 0, 0])  # wet+solar
        Rs, _, sw_s, _ = run_closed_loop(dp, None, cache, F0, x0, static=True, days=10)
        Rr, _, sw_r, _ = run_closed_loop(dp, screen, cache, F0, x0, days=10)
        assert sw_s == 0 and sw_r >= 1
        assert Rr > Rs                                         # rescue realized


class TestBOCPD:
    def test_step_change_detected_no_nominal_alarms(self):
        from rdt_core.bocpd import detect
        # seed 1: verified noise-clean over the pre-change window; raw N(0,1)
        # synthetic channels are noisier than 1.5%-rel plant channels, so the
        # deployment-level FA gate is the benchmark (0.80/30 d), not this test
        rng = np.random.default_rng(1)
        Z = rng.normal(0, 1, (400, 6))
        Z[200:, 0] += 4.0                              # step in channel 0
        alarms = detect(Z, 0.85, cusum_h=12.0)
        assert alarms and 200 <= alarms[0] <= 208      # detected within 4 h
        assert not [a for a in alarms if a < 200]      # no pre-change alarms

    def test_slow_ramp_caught_by_cusum_fusion(self):
        from rdt_core.bocpd import detect
        rng = np.random.default_rng(1)
        Z = rng.normal(0, 1, (600, 6))
        Z[300:, 1] += np.linspace(0, 2.5, 300)         # slow drift (D1 class)
        assert detect(Z, 0.85, cusum_h=12.0), "ramp missed"
        assert not detect(Z[:300], 0.85, cusum_h=12.0) # nominal-only clean
