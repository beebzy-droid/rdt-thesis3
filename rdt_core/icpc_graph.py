"""rdt_core.icpc_graph — Full ICPC process graph and G_max superstructure.

Single source of truth (lifecycle doc §5.1.1). Capacities from Table 5.1 exactly.
Every downstream artifact (DAE model, MILP constraints, scenario library, GAT
features) reads this module or its frozen JSON serialization — never hand-copies.

Units convention: capacities normalized to kg/hr total mass where sensible;
original brief units retained in the `capacity_brief` attribute for traceability.
Conversions used (flagged [est.], to verify in Phase 1 against PCA data):
  nut mass ≈ 1.2 kg/nut whole [est.]; copra yield ≈ 0.25 kg/nut [est.];
  shell ≈ 0.18 kg/nut, husk ≈ 0.40 kg/nut, water ≈ 0.20 L/nut [est.].
"""
from __future__ import annotations
import json
import networkx as nx

NODE_KINDS = ("source", "unit", "storage", "utility", "sink")

# --------------------------------------------------------------------- nodes
NODES = {
    # sources
    "SRC_NUTS":        dict(kind="source"),
    "SRC_COPRA_BUY":   dict(kind="source"),   # purchased-copra alternative feed (candidate)
    "SRC_SHELL_BUY":   dict(kind="source"),   # purchased shell for carbonizer/boiler (candidate)
    "UTIL_GENSET":     dict(kind="source"),   # diesel genset backup power (candidate; D4)
    # 7 core units — Table 5.1 exact values in capacity_brief
    "V01_RECEIVING":   dict(kind="unit", capacity_brief="50,000 nuts/hr"),
    "V02_CRACKING":    dict(kind="unit", capacity_brief="45,000 nuts/hr", efficiency="92–96%"),
    "V03_DRYING":      dict(kind="unit", capacity_brief="80 MT/day", moisture="18%→6%", residence="24–36 hr"),
    "V04_PRESS":       dict(kind="unit", capacity_brief="20 MT copra/hr", oil_yield="62–65%"),
    "V05_REFINING":    dict(kind="unit", capacity_brief="12 MT VCO/hr", spec="FFA < 0.1%"),
    "V06_CARBONIZER":  dict(kind="unit", capacity_brief="8 MT shell/day", T="800 °C", atmo="N2", cycle="4 hr batch"),
    "V07_EVAPORATOR":  dict(kind="unit", capacity_brief="5,000 L/hr", endpoint="65 °Brix", T="75 °C"),
    "V03B_SOLAR":      dict(kind="unit", candidate_node=True,
                            capacity_brief="solar dryer train [est. 40 MT/day]",
                            note="brief lists drying as solar+mech; second train enables rerouting (§1.3)"),
    # intermediate storage
    "BUF_COPRA":       dict(kind="storage"),
    "TANK_CRUDE_VCO":  dict(kind="storage"),
    "YARD_SHELL":      dict(kind="storage"),
    "SURGE_COCOWATER": dict(kind="storage"),
    # utilities (supply nodes; demand edges below)
    "UTIL_STEAM":      dict(kind="utility"),
    "UTIL_POWER":      dict(kind="utility"),
    "UTIL_CW":         dict(kind="utility"),
    "UTIL_AIR":        dict(kind="utility"),
    # sinks (product + byproduct + waste)
    "SNK_VCO":         dict(kind="sink"), "SNK_VCO_CRUDE": dict(kind="sink"),
    "SNK_MEAL":        dict(kind="sink"), "SNK_CHAR":      dict(kind="sink"),
    "SNK_CONC":        dict(kind="sink"), "SNK_COPRA_SALE": dict(kind="sink"),
    "SNK_SHELL_SALE":  dict(kind="sink"), "SNK_WASTE":     dict(kind="sink"),
    "SNK_NUT_SALE":    dict(kind="sink"),
}

# ------------------------------------------------- nominal (active) topology
# attrs: stream = process|utility; active = True in nominal operation
NOMINAL_EDGES = [
    ("SRC_NUTS", "V01_RECEIVING",       dict(stream="process")),
    ("V01_RECEIVING", "V02_CRACKING",   dict(stream="process")),
    ("V02_CRACKING", "V03_DRYING",      dict(stream="process", material="kernel")),
    ("V02_CRACKING", "YARD_SHELL",      dict(stream="process", material="shell")),
    ("V02_CRACKING", "SURGE_COCOWATER", dict(stream="process", material="coco_water")),
    ("V02_CRACKING", "SNK_WASTE",       dict(stream="process", material="husk")),
    ("V03_DRYING", "BUF_COPRA",         dict(stream="process", material="copra")),
    ("BUF_COPRA", "V04_PRESS",          dict(stream="process")),
    ("V04_PRESS", "TANK_CRUDE_VCO",     dict(stream="process", material="crude_vco")),
    ("V04_PRESS", "SNK_MEAL",           dict(stream="process", material="copra_meal")),
    ("TANK_CRUDE_VCO", "V05_REFINING",  dict(stream="process")),
    ("V05_REFINING", "SNK_VCO",         dict(stream="process", material="rbd_vco")),
    ("YARD_SHELL", "V06_CARBONIZER",    dict(stream="process")),
    ("V06_CARBONIZER", "SNK_CHAR",      dict(stream="process", material="char")),
    # PROMOTED candidate→nominal (2026-07-03 ToC finding): shell arisings ≈ 45.9 MT/day
    # vs 8 MT/day carbonizer capacity at dryer-limited feed (573% util); excess shell
    # sale is REQUIRED for steady nominal operation, not a disruption response.
    ("YARD_SHELL", "SNK_SHELL_SALE",    dict(stream="process", material="shell_excess")),
    ("SURGE_COCOWATER", "V07_EVAPORATOR", dict(stream="process")),
    ("V07_EVAPORATOR", "SNK_CONC",      dict(stream="process", material="concentrate")),
    # utility distribution (active)
    *[("UTIL_STEAM", u, dict(stream="utility")) for u in
      ("V03_DRYING", "V05_REFINING", "V07_EVAPORATOR")],
    *[("UTIL_POWER", u, dict(stream="utility")) for u in
      ("V01_RECEIVING", "V02_CRACKING", "V03_DRYING", "V04_PRESS",
       "V05_REFINING", "V06_CARBONIZER", "V07_EVAPORATOR")],
    *[("UTIL_CW", u, dict(stream="utility")) for u in ("V05_REFINING", "V07_EVAPORATOR")],
    *[("UTIL_AIR", u, dict(stream="utility")) for u in ("V02_CRACKING", "V04_PRESS")],
]

# ------------------------- superstructure candidates (installable, inactive)
# Each maps to a physically concrete reconfiguration option (lifecycle §1.3).
CANDIDATE_EDGES = [
    ("TANK_CRUDE_VCO", "SNK_VCO_CRUDE", dict(option="bypass refining — sell crude VCO when V05 lost")),
    ("YARD_SHELL", "UTIL_STEAM",        dict(option="shells → boiler fuel during steam/fuel outage")),
    ("SURGE_COCOWATER", "SNK_WASTE",    dict(option="coco-water discharge route under evaporator failure")),
    ("SRC_COPRA_BUY", "BUF_COPRA",      dict(option="purchased-copra feed under nut-supply shortfall (D1/D7)")),
    ("V02_CRACKING", "V04_PRESS",       dict(option="fresh-kernel wet route — bypass drying under dryer loss/quality shift")),
    ("BUF_COPRA", "SNK_COPRA_SALE",     dict(option="sell copra directly when press unavailable")),
    ("SURGE_COCOWATER", "SNK_CONC",     dict(option="sell/ship raw coco water unconcentrated (quality-permitting)")),
    ("V03_DRYING", "SNK_COPRA_SALE",    dict(option="divert dried copra to sale at buffer overflow")),
    ("UTIL_POWER", "UTIL_AIR",          dict(option="electric backup compressor line-up under air-system loss")),
    # ---- expansion round 1 (weeks 5–10 walkthrough), by category ----
    # bypasses
    ("SRC_NUTS", "V02_CRACKING",        dict(option="receiving bypass for pre-graded contracted lots (V01 loss)")),
    # product diverts / alternative sales
    ("V01_RECEIVING", "SNK_NUT_SALE",   dict(option="sell graded whole nuts under downstream cascade failure (D6)")),
    ("BUF_COPRA", "SNK_WASTE",          dict(option="condemned-copra divert — aflatoxin/mold rejection (D2)")),
    # alternative supply
    ("SRC_SHELL_BUY", "YARD_SHELL",     dict(option="purchased shell sustains carbonizer under nut shortfall (D1/D7)")),
    ("UTIL_GENSET", "UTIL_POWER",       dict(option="diesel genset backup under grid brownout (D4 — PH grid)")),
    # fuel / energy cross-ties
    ("V02_CRACKING", "UTIL_STEAM",      dict(option="husk as boiler solid fuel (standard PH mill practice)")),
    ("V06_CARBONIZER", "UTIL_STEAM",    dict(option="carbonizer waste-heat recovery to LP steam")),
    # rework / recycle
    ("V05_REFINING", "TANK_CRUDE_VCO",  dict(option="off-spec refined VCO recycle to crude tank")),
    # second dryer train (2-edge option group: see OPTION_GROUPS)
    ("V02_CRACKING", "V03B_SOLAR",      dict(option="solar dryer train feed", group="solar_train")),
    ("V03B_SOLAR", "BUF_COPRA",         dict(option="solar dryer train discharge", group="solar_train")),
]

# ΔG activation units: single edges by default; multi-edge groups listed here.
# A ΔG that activates only part of a group is structurally infeasible by design.
OPTION_GROUPS = {
    "solar_train": [("V02_CRACKING", "V03B_SOLAR"), ("V03B_SOLAR", "BUF_COPRA")],
}

# ------------------------------- safety exclusion pairs (HAZOP-review SEED)
# STATUS: seed list only — formal deviation review (weeks 5–10) will replace.
EXCLUSION_PAIRS = [
    (("YARD_SHELL", "UTIL_STEAM"), ("YARD_SHELL", "SNK_SHELL_SALE"),
     "single shell conveyor: cannot line up boiler-fuel and sale routes concurrently"),
    (("V02_CRACKING", "V04_PRESS"), ("SRC_COPRA_BUY", "BUF_COPRA"),
     "press feed mode conflict: wet-kernel and dry-copra modes are mutually exclusive line-ups"),
    (("TANK_CRUDE_VCO", "SNK_VCO_CRUDE"), None,
     "requires QA hold-and-release; exclusion vs. any V05 restart within same cycle — pair TBD at HAZOP"),
    (("V02_CRACKING", "UTIL_STEAM"), ("YARD_SHELL", "UTIL_STEAM"),
     "single solid-fuel feeder line to boiler: husk and shell fuel line-ups mutually exclusive"),
    (("V05_REFINING", "TANK_CRUDE_VCO"), ("TANK_CRUDE_VCO", "SNK_VCO_CRUDE"),
     "crude tank outlet manifold: recycle receipt and crude-sale dispatch line-ups conflict"),
]


def build_nominal() -> nx.DiGraph:
    """Nominal graph carries ONLY nodes referenced by nominal edges —
    candidate-only nodes (alt sources, V03B, genset) never leak in."""
    G = nx.DiGraph()
    used = {n for u, v, _ in NOMINAL_EDGES for n in (u, v)}
    for n in used:
        G.add_node(n, **NODES[n])
    for u, v, a in NOMINAL_EDGES:
        G.add_edge(u, v, active=True, **a)
    return G


def build_g_max() -> nx.DiGraph:
    G = nx.DiGraph()
    for n, a in NODES.items():
        G.add_node(n, **a)
    for u, v, a in NOMINAL_EDGES:
        G.add_edge(u, v, active=True, candidate=False, **a)
    for u, v, a in CANDIDATE_EDGES:
        G.add_edge(u, v, active=False, candidate=True, **a)
    return G


def units(G) -> set:
    """Core process units only (candidate units like V03B excluded)."""
    return {n for n, a in G.nodes(data=True)
            if a["kind"] == "unit" and not a.get("candidate_node")}


def sources(G) -> set:
    return {n for n, a in G.nodes(data=True) if a["kind"] == "source"}


def sinks(G) -> set:
    return {n for n, a in G.nodes(data=True) if a["kind"] == "sink"}


def freeze(path: str = "data/g_max.json") -> dict:
    """Serialize G_max + exclusions to the frozen JSON of record."""
    G = build_g_max()
    payload = {
        "version": "0.2.0-walkthrough-r1",
        "nodes": {n: a for n, a in G.nodes(data=True)},
        "edges": [{"u": u, "v": v, **a} for u, v, a in G.edges(data=True)],
        "exclusion_pairs_seed": [
            {"a": list(a), "b": list(b) if b else None, "basis": why}
            for a, b, why in EXCLUSION_PAIRS
        ],
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=1)
    return payload
