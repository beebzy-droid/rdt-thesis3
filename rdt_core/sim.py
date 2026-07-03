"""rdt_core.sim — SimPy ⊕ CasADi operator-splitting driver (Risk R1 architecture).

Contract (lifecycle doc §5.1.2):
  * SimPy owns the event calendar. Events are the ONLY mechanism that changes
    topology / discrete modes / parameters (here: feed rate F).
  * Between consecutive events the DAE integrates with piecewise-constant params.
  * At each event: integrator is re-called with the last state as x0 (warm start);
    IDAS re-solves consistent algebraic initialization.

This file demonstrates the pattern on the toy flowsheet with a D1-lite
disruption (step feed cut) and returns the full trajectory for validation.
"""
from __future__ import annotations
import simpy
import numpy as np
from .toy_flowsheet import ToyParams, build_dae, make_integrator


def run_scenario(events: list[tuple[float, float]], t_end: float,
                 p: ToyParams | None = None, dt_report: float = 0.5) -> dict:
    """events: list of (time [hr], new feed F [kg/hr]); must start at t=0.
    Returns dict of time grid, x(t), I(t), F_oil(t), F(t), and event log."""
    p = p or ToyParams()
    dae = build_dae(p)
    intg = make_integrator(dae, dt_report)          # fixed reporting step
    env = simpy.Environment()

    state = {"x": np.array([p.x_in, 0.0]), "z": np.array([0.0]),
             "F": events[0][1], "log": [], "t": [], "X": [], "I": [], "Foil": [], "Fr": []}

    def event_proc(env, t_evt, F_new):
        yield env.timeout(t_evt - env.now)
        state["F"] = F_new                           # discrete layer mutates parameter
        state["log"].append((env.now, F_new))

    def integrate_proc(env):
        while env.now < t_end:
            yield env.timeout(dt_report)
            res = intg(x0=state["x"], z0=state["z"], p=state["F"])
            state["x"] = np.array(res["xf"]).ravel()
            state["z"] = np.array(res["zf"]).ravel()
            state["t"].append(env.now)
            state["X"].append(state["x"][0])
            state["I"].append(state["x"][1])
            state["Foil"].append(state["z"][0])
            state["Fr"].append(state["F"])

    for t_evt, F_new in events:
        if t_evt > 0:
            env.process(event_proc(env, t_evt, F_new))
    env.process(integrate_proc(env))
    env.run(until=t_end + 1e-9)

    return {k: np.asarray(v) if isinstance(v, list) and k != "log" else v
            for k, v in state.items()}
