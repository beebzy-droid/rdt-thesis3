"""scripts/detection_benchmark.py — E10 detection benchmark (delay / false-alarm).

Observation vector (noisy, 1.5% rel. Gaussian [est.]) at every 0.5 h step from the
null-arm plant: [feed rate, F_press, F_refine, F_evap_feed, dryer outlet moisture,
press oil flow F_oil] — F_oil added 2026-07-03: quality shifts (D2 y_mult) were
INVISIBLE to the original channel set (98% miss = observability gap, not detector).
Channels z-scored against the first-72 h nominal calibration window per run.
Protocols:
  FA rate : 20 nominal (no-disruption) 30-day runs -> alarms per 30 days
  Delay   : per category, eval scenarios -> t_alarm - onset (miss if none < onset+48 h)
Grid caveat: 0.5 h observation interval floors measurable delay at 0.5 h; the
lifecycle 60 s target applies at production sampling rates.
Usage: python scripts/detection_benchmark.py <D1|D2|D3|D4|D8|FA> [threshold]
"""
import sys, time, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np
import pandas as pd
import casadi as ca

from rdt_core.plant_dae import PlantParams, wb2db
from rdt_core.disruptions import sample, dae_params, DisruptionParams
from rdt_core.compiler import compile_plant
from rdt_core.bocpd import detect
from rdt_core import icpc_graph as icpc

DT, DAYS = 0.5, 30.0
SEED_EVAL, N_EVAL = 27182, 40
NOISE = 0.015
CAL_STEPS = 144            # 72 h calibration window


def nominal_G():
    G = icpc.build_g_max()
    for u, v, a in G.edges(data=True):
        if a.get("candidate"):
            G.edges[u, v]["active"] = False
    return G


def obs_stream(dp, p, cpn, intg, F0, x0, rng):
    n = int(DAYS * 24 / DT)
    xk, zk = x0.copy(), np.zeros(2)
    O = np.empty((n, 6))
    fe = cpn.flow_edges
    ip = fe.index(("BUF_COPRA", "V04_PRESS"))
    ir = fe.index(("TANK_CRUDE_VCO", "V05_REFINING"))
    iv = fe.index(("SURGE_COCOWATER", "V07_EVAPORATOR"))
    for i in range(n):
        par = (dae_params(dp, i * DT, F0)[:6] if dp is not None
               else [F0, 1.0, 0.0, 1.0, 1.0, 1.0])
        zk = np.array(cpn.z_fn(xk, par)).ravel()
        r = intg(x0=xk, z0=zk, p=par)
        xk = np.array(r["xf"]).ravel(); zk = np.array(r["zf"]).ravel()
        fl = np.array(cpn.flow_fn(xk, zk, par)).ravel()
        O[i] = [par[0], fl[ip], fl[ir], fl[iv], xk[4], zk[0]]  # + F_oil (quality-bearing)
    O *= 1 + rng.normal(0, NOISE, O.shape)
    mu, sd = O[:CAL_STEPS].mean(0), O[:CAL_STEPS].std(0) + 1e-9
    return (O - mu) / sd


def steady_x0(p, cpn, intg, F0):
    """Warm start at TRUE steady state (fix 2026-07-03: settling transient inside
    the calibration window inflated CUSUM FA to 11.4/30 d — the drift detector was
    chasing the plant's own convergence, not disruptions)."""
    xk = np.concatenate([np.full(5, wb2db(p.x_in_wb)),
                         [F0 * 0.30 * p.tau_buf * 0.8, 2000.0, 3000.0, 1000.0], [0, 0]])
    zk = np.zeros(2)
    par = [F0, 1.0, 0.0, 1.0, 1.0, 1.0]
    for _ in range(400):                                     # 200 h nominal settle
        zk = np.array(cpn.z_fn(xk, par)).ravel()
        r = intg(x0=xk, z0=zk, p=par)
        xk = np.array(r["xf"]).ravel()
    xk[-2:] = 0.0                                            # reset accumulators
    return xk


def main(cat, thr, h=8.0):
    p = PlantParams(); F0 = p.nominal_nut_feed()
    cpn = compile_plant(nominal_G(), p)
    intg = ca.integrator("P", "idas", cpn.dae, 0.0, DT,
                         {"abstol": 1e-8, "reltol": 1e-8})
    x0 = steady_x0(p, cpn, intg, F0)
    rng = np.random.default_rng(777)
    rows, t0 = [], time.perf_counter()
    if cat == "FA":
        for k in range(20):
            Z = obs_stream(None, p, cpn, intg, F0, x0, rng)
            rows.append(dict(category="FA", seed=k, threshold=thr,
                             n_alarms=len(detect(Z, thr, cusum_h=h)), delay_hr=np.nan))
    else:
        for dp in sample(cat, N_EVAL, SEED_EVAL):
            Z = obs_stream(dp, p, cpn, intg, F0, x0, rng)
            alarms = detect(Z, thr, cusum_h=h)
            onset_i = int(dp.onset_hr / DT)
            hits = [a for a in alarms if onset_i <= a <= onset_i + int(48 / DT)]
            fa_pre = sum(1 for a in alarms if a < onset_i)
            delay = (hits[0] - onset_i) * DT if hits else np.nan
            rows.append(dict(category=cat, seed=dp.seed, threshold=thr,
                             n_alarms=fa_pre, delay_hr=delay))
    df = pd.DataFrame(rows)
    out = pathlib.Path("data/detection_bench.parquet")
    if out.exists():
        df = pd.concat([pd.read_parquet(out), df], ignore_index=True)
    df.to_parquet(out, index=False)
    g = df[(df.category == cat) & (df.threshold == thr)]
    if cat == "FA":
        print(f"FA thr={thr}: {g.n_alarms.mean():.2f} alarms / 30 d "
              f"({time.perf_counter()-t0:.0f} s)")
    else:
        print(f"{cat} thr={thr}: delay med={g.delay_hr.median():.1f} h "
              f"p90={g.delay_hr.quantile(.9):.1f} miss={g.delay_hr.isna().mean():.0%} "
              f"pre-onset FA/run={g.n_alarms.mean():.2f} ({time.perf_counter()-t0:.0f} s)")


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 0.85,
         float(sys.argv[3]) if len(sys.argv) > 3 else 8.0)
