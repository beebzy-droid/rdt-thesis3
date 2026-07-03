"""rdt_core.compiler — Graph→DAE compiler. Topology as a RUNTIME data structure.

This module is the §3.1.3 architectural contribution: given any structurally
feasible subgraph G of G_max (edge `active` flags define the topology), emit the
CasADi semi-explicit DAE, output functions, and state metadata. Applying a ΔG is
now: toggle edge flags → recompile → warm-start-remap states (Eq. 2.2 executable).

v1 scope (whitelisted option edges — compiler REFUSES unknown active candidates
rather than silently mis-modeling them, per §9.2 integrity rules):
    TANK_CRUDE_VCO→SNK_VCO_CRUDE   (crude bypass)
    V02_CRACKING→V04_PRESS         (wet-kernel route)
    SRC_COPRA_BUY→BUF_COPRA        (purchased copra)
    V02_CRACKING→V03B_SOLAR + V03B_SOLAR→BUF_COPRA   (solar dryer train, 2-edge ΔG)
Utility edges are health-multiplier semantics in v1 (no pressure-flow network yet).

Parameter vector (compiled): [F_nuts, y_mult, dx_wb, h_dry, h_press, h_ref]  — the
decision inputs u_* of the legacy hand-coded model are GONE; decisions live in the
graph. Equivalence with the legacy model is enforced by tests/test_compiler.py.
"""
from __future__ import annotations
import casadi as ca
import networkx as nx
from dataclasses import dataclass

from .plant_dae import PlantParams, wb2db

MODELED_OPTION_EDGES = {
    ("TANK_CRUDE_VCO", "SNK_VCO_CRUDE"),
    ("V02_CRACKING", "V04_PRESS"),
    ("SRC_COPRA_BUY", "BUF_COPRA"),
    ("V02_CRACKING", "V03B_SOLAR"),
    ("V03B_SOLAR", "BUF_COPRA"),
}


@dataclass
class CompiledPlant:
    dae: dict
    out_fn: ca.Function          # (x, z, p) -> [P_mass, V_php]
    state_names: list
    param_names: list
    active_options: set


def _active(G, u, v) -> bool:
    return G.has_edge(u, v) and G.edges[u, v].get("active", False)


def compile_plant(G: nx.DiGraph, p: PlantParams | None = None,
                  solar_cap_kernel: float = 2_050.0) -> CompiledPlant:
    """Compile the DAE for topology G. solar_cap_kernel [kg wet kernel/hr] is the
    V03B intake ceiling (≈40 MT copra/day equivalent [est.])."""
    p = p or PlantParams()

    # ---- admission: refuse unmodeled active candidate edges (integrity §9.2) ----
    active_opts = set()
    for u, v, a in G.edges(data=True):
        if a.get("candidate") and a.get("active"):
            if (u, v) not in MODELED_OPTION_EDGES:
                raise NotImplementedError(f"active candidate edge ({u},{v}) not in "
                                          f"v1 compiler whitelist")
            active_opts.add((u, v))
    has_crude = _active(G, "TANK_CRUDE_VCO", "SNK_VCO_CRUDE")
    has_wet = _active(G, "V02_CRACKING", "V04_PRESS")
    has_buy = _active(G, "SRC_COPRA_BUY", "BUF_COPRA")
    has_solar = (_active(G, "V02_CRACKING", "V03B_SOLAR")
                 and _active(G, "V03B_SOLAR", "BUF_COPRA"))
    if _active(G, "V02_CRACKING", "V03B_SOLAR") != _active(G, "V03B_SOLAR", "BUF_COPRA"):
        raise ValueError("solar_train is a 2-edge OPTION_GROUP; partial activation "
                         "is structurally infeasible by design")

    # ---- symbols ----
    n_c = p.n_comp
    xs = ca.SX.sym("xm", n_c)                 # primary dryer moisture chain
    xsB = ca.SX.sym("xmB", n_c) if has_solar else None
    I = ca.SX.sym("I", 4)                     # copra, vco, shell, ccw
    m_evap = ca.SX.sym("m_evap"); m_out = ca.SX.sym("m_out")
    F_oil = ca.SX.sym("F_oil"); F_conc = ca.SX.sym("F_conc")
    F_nuts = ca.SX.sym("F_nuts"); y_mult = ca.SX.sym("y_mult")
    dx_wb = ca.SX.sym("dx_wb")
    h_dry = ca.SX.sym("h_dry"); h_press = ca.SX.sym("h_press"); h_ref = ca.SX.sym("h_ref")

    # ---- front end (V01/V02, material-attributed edges) ----
    F_kernel = p.f_kernel * F_nuts
    F_shell = p.f_shell * F_nuts
    F_husk = p.f_husk * F_nuts
    F_ccw_in = p.f_water * F_nuts

    x_in_wb_eff = p.x_in_wb + dx_wb
    x_in = x_in_wb_eff / (1 - x_in_wb_eff)

    # kernel routing: primary dryer (health-scaled) -> solar (overflow, capped)
    #                 -> wet press (if active, tank-gated) -> spoil
    F_kd_A = h_dry * F_kernel
    over1 = F_kernel - F_kd_A
    F_kd_B = ca.fmin(over1, solar_cap_kernel) if has_solar else ca.SX(0)
    over2 = over1 - F_kd_B
    # tank gate (C-inf, identical to legacy)
    gate_tank = 0.5 * (1 + ca.tanh((p.I_crude_max - I[1] - p.gate_band / 2)
                                   / (p.gate_band / 4)))
    F_wet = gate_tank * over2 if has_wet else ca.SX(0)
    F_spoil = F_kernel - F_kd_A - F_kd_B - F_wet

    # ---- dryer trains: 5-CSTR chains, DESIGN-constant holdup (finding #6) ----
    Fs_design = (80_000.0 / 24) * (1 - 0.06)
    Ms = (p.tau_dry / n_c) * Fs_design

    def dryer_chain(x_chain, F_kd):
        Fs = F_kd * (1 - x_in_wb_eff)
        dx = [(Fs / Ms) * ((x_in if i == 0 else x_chain[i - 1]) - x_chain[i])
              - p.k_dry * (x_chain[i] - p.x_eq) for i in range(n_c)]
        F_cop = Fs * (1 + x_chain[-1])
        return ca.vertcat(*dx), F_cop, F_kd - F_cop

    dxs_A, F_copra_A, F_ev_A = dryer_chain(xs, F_kd_A)
    if has_solar:
        MsB = (p.tau_dry / n_c) * (solar_cap_kernel * (1 - p.x_in_wb))
        FsB = F_kd_B * (1 - x_in_wb_eff)
        dxs_B = ca.vertcat(*[(FsB / MsB) * ((x_in if i == 0 else xsB[i - 1]) - xsB[i])
                             - p.k_dry * (xsB[i] - p.x_eq) for i in range(n_c)])
        F_copra_B = FsB * (1 + xsB[-1]); F_ev_B = F_kd_B - F_copra_B
    else:
        dxs_B, F_copra_B, F_ev_B = None, ca.SX(0), ca.SX(0)
    F_copra = F_copra_A + F_copra_B

    # ---- purchased copra (deficit-following) ----
    F_copra_nom = 80_000.0 / 24
    F_buy = ca.fmax(0, F_copra_nom - F_copra) if has_buy else ca.SX(0)

    # ---- press / refining / bypass (identical port of legacy relations) ----
    F_press = ca.fmin(h_press * gate_tank * I[0] / p.tau_buf,
                      h_press * gate_tank * p.cap_press)
    F_meal = F_press - F_oil
    oil_wet = p.y_wet * y_mult * F_wet
    cake_wet = F_wet - oil_wet
    F_tank_out = I[1] / p.tau_tank
    F_refine = ca.fmin(h_ref * F_tank_out, p.cap_refine)
    F_crude_sale = (F_tank_out - F_refine) if has_crude else ca.SX(0)
    F_vco = p.y_refine * F_refine
    F_ref_loss = F_refine - F_vco
    F_carb = p.cap_carb * I[2] / (I[2] + p.K_sat)
    F_char = p.y_char * F_carb
    F_offgas = F_carb - F_char
    F_evap_feed = ca.fmin(I[3] / p.tau_surge, p.cap_evap)
    F_evap_water = F_evap_feed - F_conc

    dI = ca.vertcat(F_copra + F_buy - F_press,
                    F_oil + oil_wet - F_refine - F_crude_sale,
                    F_shell - F_carb,
                    F_ccw_in - F_evap_feed)
    F_sinks = (F_husk + F_meal + F_vco + F_ref_loss + F_char + F_offgas
               + F_conc + F_evap_water + F_crude_sale + F_spoil + cake_wet)

    ode_parts = [dxs_A] + ([dxs_B] if has_solar else []) + \
                [dI, F_ev_A + F_ev_B, F_sinks]
    x_parts = [xs] + ([xsB] if has_solar else []) + [I, m_evap, m_out]
    x = ca.vertcat(*x_parts)
    z = ca.vertcat(F_oil, F_conc)
    par = ca.vertcat(F_nuts, y_mult, dx_wb, h_dry, h_press, h_ref)
    alg = ca.vertcat(F_oil - p.y_oil * y_mult * F_press,
                     F_conc - F_evap_feed * p.brix_in / p.brix_out)
    dae = {"x": x, "z": z, "p": par, "ode": ca.vertcat(*ode_parts), "alg": alg}

    P_prod = (F_vco + F_meal + cake_wet + F_char + F_conc + F_crude_sale
              + (F_shell - F_carb))
    V_php = (p.w_vco * F_vco + p.w_meal * (F_meal + cake_wet) + p.w_char * F_char
             + p.w_conc * F_conc + p.w_crude * F_crude_sale
             + p.w_shell * (F_shell - F_carb) - p.w_copra_buy * F_buy)
    out_fn = ca.Function("prod", [x, z, par], [P_prod, V_php])

    names = [f"x_dryA_{i}" for i in range(n_c)]
    if has_solar:
        names += [f"x_dryB_{i}" for i in range(n_c)]
    names += ["I_copra", "I_vco", "I_shell", "I_ccw", "m_evap", "m_out"]
    return CompiledPlant(dae=dae, out_fn=out_fn, state_names=names,
                         param_names=["F_nuts", "y_mult", "dx_wb",
                                      "h_dry", "h_press", "h_ref"],
                         active_options=active_opts)


def apply_change(G: nx.DiGraph, edges: list[tuple], activate: bool = True):
    """Eq. 2.2: G ⊕ ΔG. Returns a NEW graph with the edge set toggled."""
    G2 = G.copy()
    for u, v in edges:
        if not G2.has_edge(u, v):
            raise KeyError(f"({u},{v}) not in G_max — piping infeasible")
        G2.edges[u, v]["active"] = activate
    return G2


def warm_start_map(x_old, names_old: list, names_new: list, defaults: dict):
    """State remap across topologies: shared states carry over (warm start);
    new states take defaults. This is the §2.4.2 re-initialization contract."""
    import numpy as np
    old = dict(zip(names_old, np.asarray(x_old).ravel()))
    return np.array([old.get(n, defaults.get(n, 0.0)) for n in names_new])
