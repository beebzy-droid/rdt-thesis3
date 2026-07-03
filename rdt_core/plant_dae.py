"""rdt_core.plant_dae — Integrated ICPC plant DAE, v0 (nominal topology, routing fidelity).

Scope (lifecycle §5.1.2): fidelity sufficient for ROUTING decisions, not equipment
design. Fixed nominal topology; graph-regenerated DAE is the Phase 1 follow-on.
All yield/split constants are planning values flagged [est.] pending PCA/plant
verification — binding per integrity rules (§9.2).

States (11 differential + 2 algebraic):
  x1..x5   dryer compartment moisture, dry basis [-]   (5-CSTR chain, k fitted
           to Table 5.1 envelope: 18%→6% wb in 24–36 h; k = 0.08293 1/hr)
  I_copra  copra buffer inventory [kg]
  I_vco    crude VCO tank [kg]
  I_shell  shell yard [kg]
  I_ccw    coconut-water surge [kg]
  m_evap_d cumulative dryer evaporation [kg]     (closure bookkeeping)
  m_out    cumulative total sink outflow [kg]    (closure bookkeeping)
  z: F_oil press oil flow [kg/hr];  F_conc evaporator concentrate flow [kg/hr]
"""
from __future__ import annotations
import casadi as ca
import numpy as np
from dataclasses import dataclass, field


def wb2db(w): return w / (1.0 - w)
def db2wb(x): return x / (1.0 + x)


@dataclass
class PlantParams:
    # --- feed & splits (mass fractions of whole nut) [est.; verify Phase 1] ---
    kg_per_nut: float = 1.2
    f_kernel: float = 0.30
    f_shell: float = 0.15
    f_husk: float = 0.35
    f_water: float = 0.20
    # --- dryer (Table 5.1 envelope, fitted) ---
    n_comp: int = 5
    k_dry: float = 0.08293          # 1/hr, fitted to 18→6% wb @ 24–36 hr
    x_eq: float = 0.040             # equilibrium moisture, dry basis [est.]
    x_in_wb: float = 0.18           # dryer inlet, wet basis (Table 5.1)
    tau_dry: float = 30.0           # design residence [hr], mid-envelope
    # --- downstream yields [est.; brief-consistent] ---
    y_oil: float = 0.63             # press: oil per kg copra (62–65% brief)
    y_refine: float = 0.97          # refining mass recovery
    y_char: float = 0.30            # char per kg shell
    brix_in: float = 0.05           # coco water feed
    brix_out: float = 0.65          # Table 5.1 endpoint
    # --- capacities (Table 5.1, converted) ---
    cap_carb: float = 8000.0 / 24   # kg shell/hr
    cap_evap: float = 5000.0        # kg/hr (≈ L/hr at ρ≈1)
    # --- buffer draw time constants [hr] ---
    tau_buf: float = 8.0
    tau_tank: float = 6.0
    tau_surge: float = 2.0
    K_sat: float = 5000.0           # carbonizer draw saturation const [kg]

    def nominal_nut_feed(self) -> float:
        """Dryer-limited nominal feed [kg nuts/hr]: 80 MT/day copra out."""
        copra = 80_000.0 / 24                       # kg/hr product @ ~6% wb
        solids = copra * (1 - 0.06)                 # dry solids
        kernel = solids / (1 - self.x_in_wb)        # wet kernel @ 18% wb
        return kernel / self.f_kernel


def build_plant_dae(p: PlantParams):
    xs = ca.SX.sym("xm", p.n_comp)                  # dryer moisture chain
    I = ca.SX.sym("I", 4)                           # copra, vco, shell, ccw
    m_evap_d = ca.SX.sym("m_evap_d")
    m_out = ca.SX.sym("m_out")
    F_oil = ca.SX.sym("F_oil")                      # algebraic
    F_conc = ca.SX.sym("F_conc")                    # algebraic
    F_nuts = ca.SX.sym("F_nuts")                    # parameter (event-set)

    # --- front end (algebraic pass-through at routing fidelity) ---
    F_kernel = p.f_kernel * F_nuts                  # @ 18% wb into dryer
    F_shell = p.f_shell * F_nuts
    F_husk = p.f_husk * F_nuts
    F_ccw_in = p.f_water * F_nuts

    # --- dryer: 5-CSTR solids chain, constant dry-solids holdup ---
    x_in = wb2db(p.x_in_wb)
    Fs = F_kernel * (1 - p.x_in_wb)                 # dry solids throughput
    Ms = (p.tau_dry / p.n_comp) * Fs                # per-compartment dry holdup
    dxs = [(Fs / Ms) * ((x_in if i == 0 else xs[i-1]) - xs[i])
           - p.k_dry * (xs[i] - p.x_eq) for i in range(p.n_comp)]
    F_copra = Fs * (1 + xs[-1])                     # wet copra out
    F_evap_dryer = F_kernel - F_copra               # water removed

    # --- buffers with first-order draws (linear ⇒ CVODE-friendly) ---
    F_press = I[0] / p.tau_buf                      # copra buffer → press
    F_meal = F_press - F_oil                        # by mass difference
    F_refine = I[1] / p.tau_tank                    # tank → refining
    F_vco = p.y_refine * F_refine
    F_ref_loss = F_refine - F_vco
    F_carb = p.cap_carb * I[2] / (I[2] + p.K_sat)   # saturating draw ≤ capacity
    F_char = p.y_char * F_carb
    F_offgas = F_carb - F_char
    F_evap_feed = ca.fmin(I[3] / p.tau_surge, p.cap_evap)
    F_evap_water = F_evap_feed - F_conc

    dI = ca.vertcat(F_copra - F_press,
                    F_oil - F_refine,
                    F_shell - F_carb,
                    F_ccw_in - F_evap_feed)

    F_sinks = (F_husk + F_meal + F_vco + F_ref_loss + F_char + F_offgas
               + F_conc + F_evap_water)             # everything leaving plant

    ode = ca.vertcat(*dxs, dI, F_evap_dryer, F_sinks)
    alg = ca.vertcat(F_oil - p.y_oil * F_press,                       # press yield
                     F_conc - F_evap_feed * p.brix_in / p.brix_out)   # solids balance
    x = ca.vertcat(xs, I, m_evap_d, m_out)
    return {"x": x, "z": ca.vertcat(F_oil, F_conc), "p": F_nuts,
            "ode": ode, "alg": alg}


def run_nominal(days: float = 30.0, dt: float = 0.5, p: PlantParams | None = None):
    """30-day nominal campaign. Returns closure error, wall time, trajectories."""
    import time
    p = p or PlantParams()
    dae = build_plant_dae(p)
    F0 = p.nominal_nut_feed()
    intg = ca.integrator("P", "idas", dae, 0.0, dt, {"abstol": 1e-8, "reltol": 1e-8})

    x_in = wb2db(p.x_in_wb)
    x0 = np.concatenate([np.full(5, x_in),                 # start wet (worst case)
                         [F0 * 0.30 * p.tau_buf * 0.8,     # buffers near steady
                          2000.0, 3000.0, 1000.0],
                         [0.0, 0.0]])
    z0 = np.array([0.0, 0.0])
    n = int(days * 24 / dt)
    T, X = [0.0], [x0]
    t0 = time.perf_counter()
    xk, zk = x0, z0
    for i in range(n):                                     # event-grid loop (SimPy slot)
        r = intg(x0=xk, z0=zk, p=F0)
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        T.append((i + 1) * dt); X.append(xk)
    wall = time.perf_counter() - t0
    X = np.array(X); T = np.array(T)

    m_in = F0 * days * 24
    d_inv = X[-1, 5:9].sum() - X[0, 5:9].sum()
    # dryer holdup water change: Ms per compartment × Δx
    Fs = F0 * 0.30 * (1 - p.x_in_wb)
    Ms = (p.tau_dry / p.n_comp) * Fs
    d_dryer_water = Ms * (X[-1, :5] - X[0, :5]).sum()
    m_accounted = X[-1, 10] + X[-1, 9] + d_inv + d_dryer_water    # out + evap + Δinv
    closure = abs(m_in - m_accounted) / m_in
    return {"closure": closure, "wall_s": wall, "T": T, "X": X, "F0": F0,
            "x_out_wb": db2wb(X[-1, 4])}


def bottleneck_table(p: PlantParams | None = None) -> list[dict]:
    """ToC-style utilization snapshot at dryer-limited nominal feed (§5.1.1)."""
    p = p or PlantParams()
    F0 = p.nominal_nut_feed()
    nuts_hr = F0 / p.kg_per_nut
    copra = 80_000.0 / 24
    rows = [
        ("V01_RECEIVING", nuts_hr, 50_000, "nuts/hr"),
        ("V02_CRACKING", nuts_hr, 45_000, "nuts/hr"),
        ("V03_DRYING", copra * 24 / 1000, 80, "MT copra/day"),
        ("V04_PRESS", copra, 20_000, "kg copra/hr"),
        ("V05_REFINING", p.y_oil * copra, 12_000, "kg VCO/hr"),
        ("V06_CARBONIZER", p.f_shell * F0 * 24 / 1000, 8, "MT shell/day"),
        ("V07_EVAPORATOR", p.f_water * F0, 5_000, "L/hr"),
    ]
    return [dict(unit=u, load=round(l, 1), capacity=c, unit_str=s,
                 util_pct=round(100 * l / c, 1)) for u, l, c, s in rows]
