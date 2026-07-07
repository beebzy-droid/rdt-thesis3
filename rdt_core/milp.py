"""rdt_core.milp — §2.3 MILP reconfiguration selector (HiGHS).

Selects the option subset maximizing predicted value-basis ΔR subject to:
  simultaneity  Σ x_k ≤ N_max            (field-crew line-up capacity)
  exclusions    x_a + x_b ≤ 1            (auto-derived from icpc_graph seed pairs)
  activation threshold: options with ŷ ≤ y_min contribute nothing and are fixed 0
    (prevents churn on noise — reversibility is handled by re-solving each cycle)
Problem size K=7 binaries → sub-ms; the §2.3 5-s budget is irrelevant at this scale
and re-verified anyway (test).
"""
from __future__ import annotations
import numpy as np
import highspy

from . import icpc_graph as icpc

# option name -> edge set (single source of truth mirrors gen_labels_topo/compiler)
OPTION_EDGES = {
    "crude_bypass": [("TANK_CRUDE_VCO", "SNK_VCO_CRUDE")],
    "wet_route":    [("V02_CRACKING", "V04_PRESS")],
    "copra_buy":    [("SRC_COPRA_BUY", "BUF_COPRA")],
    "solar_train":  [("V02_CRACKING", "V03B_SOLAR"), ("V03B_SOLAR", "BUF_COPRA")],
    "copra_sale":   [("BUF_COPRA", "SNK_COPRA_SALE")],
    "shell_boiler": [("YARD_SHELL", "UTIL_STEAM")],
    "nut_sale":     [("V01_RECEIVING", "SNK_NUT_SALE")],
}
OPTIONS = list(OPTION_EDGES)


def exclusion_pairs() -> list[tuple[str, str]]:
    """Map icpc_graph seed exclusion pairs onto wired option names."""
    edge2opt = {e: n for n, es in OPTION_EDGES.items() for e in es}
    out = []
    for a, b, _why in icpc.EXCLUSION_PAIRS:
        oa, ob = edge2opt.get(tuple(a)), edge2opt.get(tuple(b) if b else ("", ""))
        if oa and ob and oa != ob:
            out.append((oa, ob))
    return out


def select(y_hat: dict, n_max: int = 3, y_min: float = 0.005) -> list[str]:
    """y_hat: {option: predicted dR}. Returns selected option names."""
    names = [o for o in OPTIONS if y_hat.get(o, 0.0) > y_min]
    if not names:
        return []
    h = highspy.Highs(); h.silent()
    inf = highspy.kHighsInf
    for _ in names:
        h.addVar(0, 1)
    for j in range(len(names)):
        h.changeColIntegrality(j, highspy.HighsVarType.kInteger)
    h.changeObjectiveSense(highspy.ObjSense.kMaximize)
    for j, o in enumerate(names):
        h.changeColCost(j, float(y_hat[o]))
    h.addRow(-inf, n_max, len(names), np.arange(len(names)), np.ones(len(names)))
    ix = {o: j for j, o in enumerate(names)}
    for a, b in exclusion_pairs():
        if a in ix and b in ix:
            h.addRow(-inf, 1, 2, np.array([ix[a], ix[b]]), np.ones(2))
    h.run()
    sol = np.array(h.getSolution().col_value)
    return [o for j, o in enumerate(names) if sol[j] > 0.5]
