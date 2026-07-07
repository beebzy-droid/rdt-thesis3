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
            # degraded-mode ladder (§5.4.1): loose-tol retry, then 10x substep
            i_loose = ca.integrator("PL", "idas", cpn.dae, 0.0, DT,
                                    {"abstol": 1e-6, "reltol": 1e-6})
            i_sub = ca.integrator("PS", "idas", cpn.dae, 0.0, DT / 10,
                                  {"abstol": 1e-6, "reltol": 1e-6})
            intg = (intg, i_loose, i_sub)
            self._c[opts] = (cpn, intg, G)
        return self._c[opts]


def run_closed_loop(dp, screen, cache: TopologyCache, F0, x_init,
                    days=30.0, cycle_hr=1.0, static=False, r_win=72.0,
                    y_on=0.02, y_off=0.005, dwell_hr=6.0,
                    cache_slow: "TopologyCache" = None, t_regime: float = None,
                    t_enable: float = 0.0):
    """cache_slow + t_regime: hoard->deploy continuous schedule — integrate on
    cache_slow (passive draws) until t_regime, then on `cache` (fast draws).
    Same-topology state vectors are identical across param sets -> no remap.
    §5.4.2 symmetry fix 2026-07-03: RDT must ride the winning continuous policy."""
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
    use_slow = cache_slow is not None and t_regime is not None
    cur = cache_slow if use_slow else cache
    cpn, intg, _ = cur.get(active)
    xk, zk = x_init.copy(), np.zeros(2)
    V = np.empty(n)
    switches, log = 0, []
    degraded = [0, 0]                # [loose-tol retries, substep escalations]
    last_switch_t = -1e9
    dG_rows = np.stack([ft.delta_multihot(cache.edges, OPTION_EDGES[o])
                        for o in OPTIONS])
    for i in range(n):
        par = dae_params(dp, i * DT, F0)[:6]
        if use_slow and i * DT >= t_regime:
            use_slow = False
            cur = cache
            cpn, intg, _ = cur.get(active)          # identical states, no remap
        if (not static) and i % k_cycle == 0 and i > 0 \
                and i * DT >= t_enable \
                and (i * DT - last_switch_t) >= dwell_hr:
            Xv, Xe = ft.extract(cpn, cache.get(active)[2], xk, zk, par,
                                cache.nodes, cache.edges)
            yhat = dict(zip(OPTIONS, screen(Xv, Xe, dG_rows)))
            eligible = {o: y for o, y in yhat.items()
                        if y > y_on or (o in active and y > y_off)}
            chosen = frozenset(select(eligible, y_min=0.0)) | (active & STATEFUL)
            if chosen != active:
                last_switch_t = i * DT
                c_new, i_new, _ = cur.get(chosen)
                defaults = {f"x_dryB_{j}": wb2db(p.x_in_wb) for j in range(5)}
                xk = warm_start_map(xk, cpn.state_names, c_new.state_names, defaults)
                cpn, intg = c_new, i_new
                switches += 1
                log.append((i * DT, sorted(chosen)))
                active = chosen
        zk = np.array(cpn.z_fn(xk, par)).ravel()    # exact consistent init
        try:
            r = intg[0](x0=xk, z0=zk, p=par)
        except RuntimeError:
            try:
                r = intg[1](x0=xk, z0=zk, p=par)     # ladder 1: loose tol
                degraded[0] += 1
            except RuntimeError:                     # ladder 2: 10x substep
                xs, zs = xk, zk
                for _ in range(10):
                    rr = intg[2](x0=xs, z0=zs, p=par)
                    xs = np.array(rr["xf"]).ravel(); zs = np.array(rr["zf"]).ravel()
                r = {"xf": xs, "zf": zs}
                degraded[1] += 1
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        V[i] = float(cpn.out_fn(xk, zk, par)[1])
    t = np.arange(1, n + 1) * DT
    pre = (t > dp.onset_hr - 24) & (t <= dp.onset_hr)
    win = (t > dp.onset_hr) & (t <= dp.onset_hr + r_win)
    V0 = V[pre].mean()
    R = float(np.mean(V[win] / V0))
    # TTR80, corrected semantics (gen_pilot protocol): measured from first
    # impairment; never impaired -> 0; impaired, no 6 h-sustained return -> NaN
    ratio = V / V0
    post = np.where(t > dp.onset_hr)[0]
    k6 = int(6 / DT)
    below = post[ratio[post] < 0.8]
    if below.size == 0:
        ttr80 = 0.0
    else:
        ttr80 = np.nan
        for j in post[post >= below[0]]:
            if j + k6 <= n and np.all(ratio[j:j + k6] >= 0.8):
                ttr80 = t[j] - dp.onset_hr
                break
    return R, ttr80, switches, {"log": log, "degraded": degraded}


def strong_params(p: PlantParams | None = None) -> PlantParams:
    """§5.4.2 STRONG static comparator: capacity-greedy inventory deployment on the
    FIXED topology — buffered material is run down aggressively inside the recovery
    window instead of at nominal draw pace. tau values [est.]: fastest field-
    plausible line-up. RDT arm runs ON TOP of the same policy so dR isolates the
    marginal value of topology adaptation."""
    import dataclasses
    p = p or PlantParams()
    return dataclasses.replace(p, tau_buf=1.5, tau_tank=1.5, tau_surge=1.0)
