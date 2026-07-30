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
    # --- re-initialization contract (added 2026-07-13) -------------------------
    # cold_start=False reproduces the historical behaviour exactly: a newly
    # activated train is hot-started and discharges as soon as feed arrives, so
    # its transition is set by flow redistribution rather than by residence. That
    # is optimistic, and scripts/tau_sweep.py showed it makes the breakeven
    # duration independent of tau_dry (theory Section 5.1).
    # cold_start=True adds a per-train commissioning availability state a in
    # [0,1] with da/dt = (1-a)/tau_commission, ramping the train's intake as it
    # fills and establishes a moisture profile. a is initialized to 0 on
    # activation (warm_start_map already defaults absent states to 0.0), so the
    # transition becomes genuinely residence-gated.
    cold_start: bool = False
    tau_commission_mult: float = 1.0  # tau_commission = mult * tau_dry
    # --- downstream yields [est.; brief-consistent] ---
    y_oil: float = 0.63             # press: oil per kg copra (62–65% brief)
    y_refine: float = 0.97          # refining mass recovery
    y_char: float = 0.30            # char per kg shell
    brix_in: float = 0.05           # coco water feed
    brix_out: float = 0.65          # Table 5.1 endpoint
    # --- capacities (Table 5.1, converted) ---
    cap_carb: float = 8000.0 / 24   # kg shell/hr
    cap_evap: float = 5000.0        # kg/hr (≈ L/hr at ρ≈1)
    # --- product VALUE weights, PHP/kg [est., price-proxy; verify: PCA price
    #     monitors + plant interviews. Margin = price - var.cost is the Phase 5
    #     refinement; ordering is robust to the proxy] ---
    w_vco: float = 200.0
    w_crude: float = 140.0
    w_meal: float = 22.0
    w_char: float = 32.0
    w_conc: float = 100.0
    w_shell: float = 8.0
    w_copra_buy: float = 40.0       # purchased copra COST, PHP/kg [est.; verify PCA copra price]
    w_copra_sale: float = 38.0      # copra SALE price, PHP/kg [est.; buy-sale spread 2]
    w_fuel_offset: float = 12.0     # shell-as-boiler-fuel value, PHP/kg [est.; vs sale 8]
    w_nut: float = 9.0              # whole graded nut sale, PHP/kg [est.; ~farmgate]
    buy_cap_frac: float = 1e9       # purchased-copra market availability cap, as
                                    # fraction of nominal copra rate [est.; 1e9 =
                                    # uncapped legacy behavior. Finding #25: regional
                                    # disruptions constrain the copra market too]
    y_wet: float = 0.30             # wet-kernel press oil yield [est.; vs 0.63 dry route]
    # --- capacity/storage constraints (exposed by paired demo 2026-07-03:
    #     unbounded tank + uncapped drawdown made static arm unphysically strong) ---
    cap_press: float = 20_000.0     # kg copra/hr (Table 5.1)
    cap_refine: float = 12_000.0    # kg VCO/hr (Table 5.1)
    I_crude_max: float = 50_000.0   # kg ≈ 24 h nominal crude make [est.; verify tankage]
    gate_band: float = 5_000.0      # kg, smooth full-tank press throttle band
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
    y_mult = ca.SX.sym("y_mult")                    # D2/D8: press yield multiplier
    dx_wb = ca.SX.sym("dx_wb")                      # D2/D8: inlet moisture shift, wb
    h_dry = ca.SX.sym("h_dry")                      # D3/D4: dryer availability [0,1]
    h_press = ca.SX.sym("h_press")                  # D3/D4: press availability [0,1]
    h_ref = ca.SX.sym("h_ref")                      # D3/D4: refining availability [0,1]
    u_crude = ca.SX.sym("u_crude")                  # ΔG: crude-VCO sale bypass {0,1}
    u_wet = ca.SX.sym("u_wet")                      # ΔG: wet-kernel route V02→V04 {0,1}
    u_buy = ca.SX.sym("u_buy")                      # ΔG: purchased copra → buffer {0,1}

    # --- front end (algebraic pass-through at routing fidelity) ---
    F_kernel = p.f_kernel * F_nuts                  # @ 18% wb into dryer
    F_shell = p.f_shell * F_nuts
    F_husk = p.f_husk * F_nuts
    F_ccw_in = p.f_water * F_nuts

    # --- dryer: 5-CSTR solids chain, constant dry-solids holdup ---
    x_in_wb_eff = p.x_in_wb + dx_wb
    x_in = x_in_wb_eff / (1 - x_in_wb_eff)
    F_kernel_dry = h_dry * F_kernel
    # wet route is gated by tank headroom too (fix 2026-07-03: ungated wet oil
    # drove I_vco onto the gate kink -> IDACalcIC linesearch failure; also the
    # physics: no operator presses into a full crude tank)
    F_wet_raw = u_wet * (F_kernel - F_kernel_dry)
    F_spoil_pre = F_kernel - F_kernel_dry - F_wet_raw
    Fs = F_kernel_dry * (1 - x_in_wb_eff)                 # dry solids throughput
    Ms = (p.tau_dry / p.n_comp) * Fs                # per-compartment dry holdup
    dxs = [(Fs / Ms) * ((x_in if i == 0 else xs[i-1]) - xs[i])
           - p.k_dry * (xs[i] - p.x_eq) for i in range(p.n_comp)]
    F_copra = Fs * (1 + xs[-1])                     # wet copra out
    F_evap_dryer = F_kernel - F_copra               # water removed

    # --- buffers with first-order draws (linear ⇒ CVODE-friendly) ---
    F_copra_nom = 80_000.0 / 24                     # Table 5.1 design copra rate
    F_buy = u_buy * ca.fmax(0, F_copra_nom - F_copra)   # ΔG: buy the deficit
    # C-infinity gate (tanh) replaces C0 clip: IDAS BDF + calc_ic robust at band edge
    gate_tank = 0.5 * (1 + ca.tanh((p.I_crude_max - I[1] - p.gate_band / 2)
                                   / (p.gate_band / 4)))
    F_press = ca.fmin(h_press * gate_tank * I[0] / p.tau_buf,
                      h_press * gate_tank * p.cap_press)   # full tank throttles press
    F_wet = gate_tank * F_wet_raw                   # gated wet line-up
    F_spoil = F_spoil_pre + (F_wet_raw - F_wet)     # ungated surplus spoils
    F_meal = F_press - F_oil                        # by mass difference
    F_tank_out = I[1] / p.tau_tank                  # crude tank draw demand
    F_refine = ca.fmin(h_ref * F_tank_out, p.cap_refine)   # V05 capacity-capped
    F_crude_sale = u_crude * (F_tank_out - F_refine)        # ΔG: sell what V05 can't take
    F_vco = p.y_refine * F_refine
    F_ref_loss = F_refine - F_vco
    oil_wet = p.y_wet * y_mult * F_wet              # wet route: lower yield
    cake_wet = F_wet - oil_wet                      # wet cake, meal-value proxy [est.]
    F_carb = p.cap_carb * I[2] / (I[2] + p.K_sat)   # saturating draw ≤ capacity
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

    ode = ca.vertcat(*dxs, dI, F_evap_dryer, F_sinks)
    alg = ca.vertcat(F_oil - p.y_oil * y_mult * F_press,             # press yield
                     F_conc - F_evap_feed * p.brix_in / p.brix_out)   # solids balance
    x = ca.vertcat(xs, I, m_evap_d, m_out)
    z = ca.vertcat(F_oil, F_conc)
    par = ca.vertcat(F_nuts, y_mult, dx_wb, h_dry, h_press, h_ref, u_crude, u_wet, u_buy)
    dae = {"x": x, "z": z, "p": par, "ode": ode, "alg": alg}
    # outputs (separate: ca.integrator() rejects unknown dict keys):
    #   P_mass [kg/hr] saleable mass;  V_php [PHP/hr] value-weighted throughput
    #   (Eq. 2.16 margin-weighted option — MANDATORY per finding #3, 2026-07-03)
    P_prod = (F_vco + F_meal + cake_wet + F_char + F_conc + F_crude_sale
              + (F_shell - F_carb))
    F_shell_x = ca.fmax(0, F_shell - F_carb)         # fmax fix (see compiler.py)
    V_php = (p.w_vco * F_vco + p.w_meal * (F_meal + cake_wet) + p.w_char * F_char
             + p.w_conc * F_conc + p.w_crude * F_crude_sale
             + p.w_shell * F_shell_x - p.w_copra_buy * F_buy)
    out_fn = ca.Function("prod", [x, z, par], [P_prod, V_php])
    return dae, out_fn


def run_nominal(days: float = 30.0, dt: float = 0.5, p: PlantParams | None = None):
    """30-day nominal campaign. Returns closure error, wall time, trajectories."""
    import time
    p = p or PlantParams()
    dae, _out = build_plant_dae(p)
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
        r = intg(x0=xk, z0=zk, p=[F0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0])
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
