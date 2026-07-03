"""rdt_core.toy_flowsheet — 3-unit analytical validation flowsheet (Risk R1 gate).

Flowsheet:  SOURCE ──F──▶ DRYER (CSTR moisture dynamics) ──▶ PRESS (algebraic yield) ──▶ SINK

Semi-explicit index-1 DAE (Eqs. 2.12–2.13 of the lifecycle doc):
  Differential:
      dx/dt = (F/M) * (x_in − x) − k·x        # dryer outlet moisture, dry basis
      dI/dt = η·F_c − F_oil_draw               # crude-oil tank inventory
  Algebraic:
      0 = F_oil − η · F_c                      # press yield relation
where F_c = F (dryer mass holdup constant, throughput passes through).

Closed-form steady state (the analytical truth the simulator must match):
      x_ss     = x_in / (1 + k·M/F)  = x_in / (1 + k·τ)
      F_oil_ss = η · F
      I_ss     : ramp with slope (η·F − F_oil_draw)  → checked as linear-ramp slope.

Every symbol is unit-annotated in comments; SI-consistent (kg, hr).
"""
from __future__ import annotations
import casadi as ca
import numpy as np
from dataclasses import dataclass


@dataclass
class ToyParams:
    M: float = 40_000.0     # dryer solids holdup [kg]  (≈ 80 MT/day * 0.5 day residence)
    k: float = 0.08         # first-order drying rate constant [1/hr]
    x_in: float = 0.18      # inlet moisture, dry basis [-]
    eta: float = 0.63       # press oil yield [-]  (mid of 62–65% brief range)
    F_oil_draw: float = 0.0 # downstream draw from oil tank [kg/hr]


def analytical_steady_state(F: float, p: ToyParams) -> dict:
    tau = p.M / F                                    # residence time [hr]
    return {
        "x_ss": p.x_in / (1.0 + p.k * tau),          # [-]
        "F_oil_ss": p.eta * F,                       # [kg/hr]
        "I_slope": p.eta * F - p.F_oil_draw,         # [kg/hr]
    }


def build_dae(p: ToyParams):
    """Return CasADi semi-explicit DAE dict + symbols. F enters as parameter u
    so the SimPy event layer can change it at events without rebuilding."""
    x = ca.SX.sym("x")          # dryer moisture [-]           (differential)
    I = ca.SX.sym("I")          # oil tank inventory [kg]      (differential)
    F_oil = ca.SX.sym("F_oil")  # press oil flow [kg/hr]       (algebraic z)
    F = ca.SX.sym("F")          # feed rate [kg/hr]            (parameter — event-set)

    ode = ca.vertcat(
        (F / p.M) * (p.x_in - x) - p.k * x,     # dx/dt
        p.eta * F - p.F_oil_draw,               # dI/dt (uses exact relation; alg checked)
    )
    alg = F_oil - p.eta * F                     # 0 = g(...)  index-1, trivially solvable
    return {"x": ca.vertcat(x, I), "z": F_oil, "p": F, "ode": ode, "alg": alg}


def make_integrator(dae: dict, dt: float):
    """IDAS integrator over one inter-event window of length dt [hr].
    BDF, adaptive step internally; consistent algebraic initialization is
    performed by IDAS via calc_ic at each call — the operator-splitting contract."""
    return ca.integrator("F", "idas", dae, 0.0, dt,
                         {"abstol": 1e-10, "reltol": 1e-10})
