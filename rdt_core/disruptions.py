"""rdt_core.disruptions — D1–D8 disruption samplers (lifecycle Table 5.2) with
Latin Hypercube stratification, and disturbance-trajectory evaluation.

Parameter RANGES are Table 5.2 exact. Category→DAE mapping status (v0):
  MAPPED to plant_dae parameters [F_nuts, y_mult, dx_wb]:
    D1 (supply drop), D2 (quality), D7 (drought window), D8 (D1×D2 joint)
  DEFERRED to topology-DAE (unit health / utility states — next commit):
    D3, D4, D5, D6  — samplers implemented, runner mapping raises NotImplementedError.
All draws seeded; identical (category, seed) → bit-identical parameter sets (CRN).
"""
from __future__ import annotations
import numpy as np
from dataclasses import dataclass, asdict
from scipy.stats import qmc


@dataclass
class DisruptionParams:
    category: str
    seed: int
    severity: float          # fractional supply/capacity loss [-]
    onset_hr: float          # disruption start within sim window [hr]
    ramp_hr: float           # onset ramp length [hr]
    duration_hr: float       # full-severity hold [hr]
    recovery_tau_hr: float   # exponential recovery time constant [hr]
    dx_wb: float = 0.0       # inlet-moisture shift, wet basis points [-]
    y_mult: float = 1.0      # press oil-yield multiplier [-]
    unit: str = ""           # D3: failed unit in {dry, press, refine}


# Table 5.2 ranges. Each entry: dict of param -> (lo, hi). [verify] anchors per doc.
RANGES = {
    "D1": dict(severity=(0.30, 0.95), ramp_hr=(0, 48), duration_hr=(72, 1440),
               recovery_tau_hr=(24, 240)),
    "D2": dict(severity=(0.0, 0.0), ramp_hr=(0, 24), duration_hr=(72, 720),
               recovery_tau_hr=(24, 120), dx_wb=(0.02, 0.08), y_mult=(0.80, 0.95)),
    "D3": dict(severity=(1.0, 1.0), ramp_hr=(0, 0), duration_hr=(8, 72),
               recovery_tau_hr=(1, 1)),          # unit TTR lognormal in topology-DAE
    "D4": dict(severity=(0.3, 1.0), ramp_hr=(0, 0), duration_hr=(0.5, 72),
               recovery_tau_hr=(1, 6)),
    "D5": dict(severity=(1.0, 1.0), ramp_hr=(0, 0), duration_hr=(24, 336),
               recovery_tau_hr=(1, 24)),
    "D6": dict(severity=(1.0, 1.0), ramp_hr=(0, 24), duration_hr=(8, 144),
               recovery_tau_hr=(6, 48)),
    "D7": dict(severity=(0.15, 0.40), ramp_hr=(0, 0), duration_hr=(720, 720),
               recovery_tau_hr=(720, 720)),      # 30-day window inside drought
    "D8": dict(severity=(0.30, 0.95), ramp_hr=(0, 48), duration_hr=(72, 1440),
               recovery_tau_hr=(24, 240), dx_wb=(0.02, 0.08), y_mult=(0.80, 0.95)),
}
MAPPED_V0 = ("D1", "D2", "D3", "D4", "D7", "D8")
D3_UNITS = ("dry", "press", "refine")   # failure-rate weights uniform [est.]
ONSET_RANGE = (48.0, 120.0)   # onset inside a 30-day window, after warm-up


def sample(category: str, n: int, seed: int) -> list[DisruptionParams]:
    """LHS-stratified draw of n parameter sets. Deterministic in (category, n, seed)."""
    keys = list(RANGES[category].keys())
    dims = len(keys) + 1                                      # + onset
    u = qmc.LatinHypercube(d=dims, seed=seed).random(n)       # stratified U(0,1)
    out = []
    for i in range(n):
        kw = {}
        for j, k in enumerate(keys):
            lo, hi = RANGES[category][k]
            kw[k] = lo + (hi - lo) * u[i, j]
        onset = ONSET_RANGE[0] + (ONSET_RANGE[1] - ONSET_RANGE[0]) * u[i, -1]
        dp = DisruptionParams(category=category, seed=seed * 100_000 + i,
                              onset_hr=onset, **kw)
        if category == "D3":
            dp.unit = D3_UNITS[i % len(D3_UNITS)]     # stratified unit assignment
        out.append(dp)
    return out


def feed_multiplier(dp: DisruptionParams, t: float) -> float:
    """Piecewise supply profile: 1 → ramp down to (1−sev) → hold → exp recovery."""
    t0, r, d = dp.onset_hr, dp.ramp_hr, dp.duration_hr
    if t < t0:
        return 1.0
    if t < t0 + r:
        return 1.0 - dp.severity * (t - t0) / max(r, 1e-9)
    if t < t0 + r + d:
        return 1.0 - dp.severity
    return 1.0 - dp.severity * np.exp(-(t - t0 - r - d) / dp.recovery_tau_hr)


def quality_shift(dp: DisruptionParams, t: float) -> tuple[float, float]:
    """(dx_wb, y_mult) trajectory — quality tracks the same disruption envelope."""
    if dp.dx_wb == 0.0 and dp.y_mult == 1.0:
        return 0.0, 1.0
    depth = (1.0 - feed_multiplier(dp, t)) / max(dp.severity, 1e-9) \
        if dp.severity > 0 else (1.0 if dp.onset_hr <= t else 0.0)
    depth = min(max(depth, 0.0), 1.0)
    return dp.dx_wb * depth, 1.0 - (1.0 - dp.y_mult) * depth


def dae_params(dp: DisruptionParams, t: float, F0: float,
               u_crude: float = 0.0) -> list[float]:
    """Map to plant_dae 7-vector [F_nuts, y_mult, dx_wb, h_dry, h_press, h_ref, u_crude].
    u_crude is the ΔG decision input (0 = static twin, 1 = bypass active)."""
    if dp.category not in MAPPED_V0:
        raise NotImplementedError(f"{dp.category} requires full topology-DAE")
    h = {"dry": 1.0, "press": 1.0, "refine": 1.0}
    fm, dx, ym = 1.0, 0.0, 1.0
    if dp.category in ("D1", "D7", "D8"):
        fm = feed_multiplier(dp, t)
    if dp.category in ("D2", "D8"):
        dx, ym = quality_shift(dp, t)
    if dp.category == "D3":
        in_outage = dp.onset_hr <= t < dp.onset_hr + dp.duration_hr
        h[dp.unit] = 0.0 if in_outage else 1.0        # hard outage, TTR = duration
    if dp.category == "D4":
        depth = 1.0 - feed_multiplier(dp, t)          # reuse envelope
        for k in h:
            h[k] = 1.0 - depth                        # utility derates all units
        fm = 1.0
    return [F0 * fm, ym, dx, h["dry"], h["press"], h["refine"], u_crude]
