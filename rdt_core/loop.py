"""rdt_core.loop — Recurrent closed-loop RDT (Finding #13 protocol).

Every decision cycle: extract state features → GBT screen predicts per-option ΔR
→ MILP selects subset → topology switch via compile-cache + warm-start remap →
continue integration. Decisions are RECURRENT: options deselect when predicted
value drops (stateless routes reverse freely); STATEFUL options (solar_train:
+5 holdup states) LATCH once activated — deactivation would delete in-transit
mass (documented v0 limitation; real dryer trains are not flipped hourly).

Static comparator = identical loop with empty selection every cycle.
"""
from __future__ import annotations
import numpy as np
import casadi as ca

from .plant_dae import PlantParams, wb2db
from .disruptions import dae_params
from .compiler import compile_plant, apply_change, warm_start_map
from . import icpc_graph as icpc
from . import features as ft
from .milp import OPTION_EDGES, OPTIONS, select

DT = 0.5
STATEFUL = {"solar_train"}          # latched once on


class TopologyCache:
    def __init__(self, p: PlantParams):
        self.p = p
        self._c = {}
        _, self.nodes, self.edges = ft.universe()

    def get(self, opts: frozenset):
        if opts not in self._c:
            G = icpc.build_g_max()
            for u, v, a in G.edges(data=True):
                if a.get("candidate"):
                    G.edges[u, v]["active"] = False
            for o in opts:
                G = apply_change(G, OPTION_EDGES[o])
            cpn = compile_plant(G, self.p)
            intg = ca.integrator("P", "idas", cpn.dae, 0.0, DT,
                                 {"abstol": 1e-8, "reltol": 1e-8})
            self._c[opts] = (cpn, intg, G)
        return self._c[opts]


def run_closed_loop(dp, screen, cache: TopologyCache, F0, x_init,
                    days=30.0, cycle_hr=1.0, static=False, r_win=72.0,
                    y_on=0.02, y_off=0.005, dwell_hr=6.0):
    """Churn control (2026-07-03, exposed by first loop smoke: 17–63 switches/ep):
    hysteresis — activate at ŷ > y_on, retain while ŷ > y_off — plus a post-switch
    decision freeze of dwell_hr. Operational plausibility is a gated endpoint
    (lifecycle §5.4.3), not a nice-to-have."""
    """screen: callable(Xv, Xe, dG_matrix[K,50]) -> yhat[K] per option, or None.
    Returns (R_php, n_switches, activation_log)."""
    p = cache.p
    n = int(days * 24 / DT)
    k_cycle = max(1, int(cycle_hr / DT))
    active: frozenset = frozenset()
    cpn, intg, _ = cache.get(active)
    xk, zk = x_init.copy(), np.zeros(2)
    V = np.empty(n)
    switches, log = 0, []
    last_switch_t = -1e9
    dG_rows = np.stack([ft.delta_multihot(cache.edges, OPTION_EDGES[o])
                        for o in OPTIONS])
    for i in range(n):
        par = dae_params(dp, i * DT, F0)[:6]
        if (not static) and i % k_cycle == 0 and i > 0 \
                and (i * DT - last_switch_t) >= dwell_hr:
            Xv, Xe = ft.extract(cpn, cache.get(active)[2], xk, zk, par,
                                cache.nodes, cache.edges)
            yhat = dict(zip(OPTIONS, screen(Xv, Xe, dG_rows)))
            eligible = {o: y for o, y in yhat.items()
                        if y > y_on or (o in active and y > y_off)}
            chosen = frozenset(select(eligible, y_min=0.0)) | (active & STATEFUL)
            if chosen != active:
                last_switch_t = i * DT
                c_new, i_new, _ = cache.get(chosen)
                defaults = {f"x_dryB_{j}": wb2db(p.x_in_wb) for j in range(5)}
                xk = warm_start_map(xk, cpn.state_names, c_new.state_names, defaults)
                cpn, intg = c_new, i_new
                switches += 1
                log.append((i * DT, sorted(chosen)))
                active = chosen
        r = intg(x0=xk, z0=zk, p=par)
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        V[i] = float(cpn.out_fn(xk, zk, par)[1])
    t = np.arange(1, n + 1) * DT
    pre = (t > dp.onset_hr - 24) & (t <= dp.onset_hr)
    win = (t > dp.onset_hr) & (t <= dp.onset_hr + r_win)
    return float(np.mean(V[win] / V[pre].mean())), switches, log
