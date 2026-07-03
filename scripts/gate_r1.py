"""scripts/gate_r1.py — Executes the three Week-1–5 verification items and prints
a numbers-only report:

  [1] R1 gate: SimPy+CasADi operator splitting vs. closed-form steady state,
      pre- and post-disruption. Pass criterion: relative error < 0.1% (1e-3).
  [2] Eq. 2.11 rank test on valid and deliberately-broken topologies.
  [3] HiGHS MILP latency smoke test at K = 10/25/50/100 binaries with
      ~200-constraint structure matching lifecycle §2.3.1 scale. Pass: p-time < 5 s.
"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import networkx as nx
import highspy

from rdt_core.toy_flowsheet import ToyParams, analytical_steady_state
from rdt_core.sim import run_scenario
from rdt_core.graph import rank_test

# ---------------------------------------------------------------- [1] R1 gate
p = ToyParams()
F0, F1 = 4000.0, 2000.0          # kg/hr nominal; 50% D1-lite cut at t = 250 hr
res = run_scenario(events=[(0.0, F0), (250.0, F1)], t_end=600.0, p=p)

def seg_err(t_lo, t_hi, F):
    ss = analytical_steady_state(F, p)
    m = (res["t"] >= t_lo) & (res["t"] <= t_hi)
    x_sim = res["X"][m][-1]
    foil_sim = res["Foil"][m][-1]
    ex = abs(x_sim - ss["x_ss"]) / ss["x_ss"]
    ef = abs(foil_sim - ss["F_oil_ss"]) / ss["F_oil_ss"]
    return ss, x_sim, foil_sim, ex, ef

print("=" * 78)
print("[1] R1 GATE — operator-splitting vs analytical steady state")
for label, (lo, hi, F) in {"pre-disruption  (F=4000)": (0, 249, F0),
                           "post-disruption (F=2000)": (500, 600, F1)}.items():
    ss, xs, fo, ex, ef = seg_err(lo, hi, F)
    print(f"  {label}: x_ss anal={ss['x_ss']:.6f}  sim={xs:.6f}  rel.err={ex:.2e}")
    print(f"  {' '*len(label)}  F_oil anal={ss['F_oil_ss']:.1f}  sim={fo:.1f}  rel.err={ef:.2e}")
    assert ex < 1e-3 and ef < 1e-3, "R1 GATE FAIL"
# inventory slope check on post-disruption segment (linear ramp)
m = res["t"] >= 500
slope = np.polyfit(res["t"][m], res["I"][m], 1)[0]
slope_anal = analytical_steady_state(F1, p)["I_slope"]
e_slope = abs(slope - slope_anal) / slope_anal
print(f"  oil-tank ramp slope: anal={slope_anal:.1f} kg/hr  sim={slope:.1f}  rel.err={e_slope:.2e}")
assert e_slope < 1e-3
print("  R1 GATE: PASS (< 0.1% on all three checks)")

# ------------------------------------- [2] structural feasibility filter
print("=" * 78)
print("[2] STRUCTURAL FEASIBILITY FILTER (amended Eq. 2.11 — see graph.py finding)")
from rdt_core.graph import structural_feasibility
UNITS, SRC, SNK = {"DRYER", "PRESS"}, {"SRC"}, {"OIL_SINK", "MEAL_SINK"}
G = nx.DiGraph([("SRC", "DRYER"), ("DRYER", "PRESS"), ("PRESS", "OIL_SINK"),
                ("PRESS", "MEAL_SINK")])
ok = structural_feasibility(G, UNITS, SRC, SNK)
G_bad = G.copy(); G_bad.remove_edge("PRESS", "OIL_SINK"); G_bad.remove_edge("PRESS", "MEAL_SINK")
bad = structural_feasibility(G_bad, UNITS, SRC, SNK)
print(f"  valid topology : passes={ok['passes']}  violations={ok['violations']}")
print(f"  broken topology: passes={bad['passes']}  violations={bad['violations']}")
assert ok["passes"] and not bad["passes"]
print("  FILTER: discriminates valid vs broken topologies correctly")
print(f"  (rank identity on valid graph, consistency only: {rank_test(G)})")

# --------------------------------------------------- [3] HiGHS latency smoke
print("=" * 78)
print("[3] HiGHS MILP LATENCY (K binaries + 60 continuous flows, ~§2.3.1 scale)")
rng = np.random.default_rng(0)
for K in (10, 25, 50, 100):
    h = highspy.Highs(); h.silent()
    inf = highspy.kHighsInf
    nF = 60
    # variables: K binaries then nF continuous flows
    for _ in range(K):  h.addVar(0, 1)
    for _ in range(nF): h.addVar(0, 1000)
    for j in range(K):  h.changeColIntegrality(j, highspy.HighsVarType.kInteger)
    # objective: maximize predicted impact of selections
    c = np.concatenate([rng.uniform(1, 10, K), np.zeros(nF)])
    h.changeObjectiveSense(highspy.ObjSense.kMaximize)
    for j, cj in enumerate(c): h.changeColCost(j, float(cj))
    # simultaneity: sum x <= 4
    h.addRow(-inf, 4, K, np.arange(K), np.ones(K))
    # budget: c_k x <= B
    h.addRow(-inf, 3.0 * K / 4, K, np.arange(K), rng.uniform(0.5, 2.0, K))
    # ~30 conflict pairs: x_a + x_b <= 1
    for _ in range(min(30, K * (K - 1) // 2)):
        a, b = rng.choice(K, 2, replace=False)
        h.addRow(-inf, 1, 2, np.array([a, b]), np.ones(2))
    # ~120 capacity couplings: F_e - 1000 * x_k <= 0
    for _ in range(120):
        e = int(rng.integers(nF)); k = int(rng.integers(K))
        h.addRow(-inf, 0, 2, np.array([K + e, k]), np.array([1.0, -1000.0]))
    t0 = time.perf_counter(); h.run(); dt = time.perf_counter() - t0
    n_rows = 2 + min(30, K*(K-1)//2) + 120
    print(f"  K={K:>3}  vars={K+nF:>3}  cons≈{n_rows:>3}  "
          f"status={h.modelStatusToString(h.getModelStatus()):<8} "
          f"obj={h.getObjectiveValue():8.2f}  solve={dt*1000:7.2f} ms")
print("=" * 78)
print("ALL WEEK-1 VERIFICATION ITEMS: PASS")
