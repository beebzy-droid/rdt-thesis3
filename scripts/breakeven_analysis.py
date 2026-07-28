"""scripts/breakeven_analysis.py — empirical test of the transition-dynamics theory.

Tests the propositions of thesis/theory_transition_dynamics.md against the
committed per-option label sets.

Proposition 1 predicts, for disruption duration D below the evaluation horizon T,
    dR_k(D) = (gamma_k / T) * (D - D*_k),
i.e. gain is LINEAR in duration with a zero at the breakeven D*_k.

Corollary 1.1 predicts the gain SATURATES for D >= T, because a disruption that
outlasts the window contributes no further rescue time. Together these give a
piecewise linear-then-flat profile, which is falsifiable: if the D >= T branch has
a significantly non-zero slope, the model of Section 1 is wrong.

Outputs, per option:
  - D* estimate with a percentile bootstrap CI
  - slope below and above the horizon (the saturation test)
  - the fraction of sampled disruptions exceeding the breakeven, Pr(D > D*),
    which is the quantity the regional design criterion of Section 6 turns on

Usage: python scripts/breakeven_analysis.py [--boot 5000] [--horizon 72]
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)

import numpy as np
import pandas as pd

LABEL_SETS = ["data/labels_v0.parquet", "data/labels_topo.parquet"]


def load_labels():
    """Concatenate the committed per-option label sets, keeping the columns the
    theory needs. Both sets carry the same schema for these fields."""
    frames = []
    for path in LABEL_SETS:
        p = pathlib.Path(path)
        if not p.exists():
            print(f"  note: {path} absent, skipping")
            continue
        d = pd.read_parquet(p)
        need = {"option", "duration_hr", "R_null", "R_opt"}
        if not need.issubset(d.columns):
            print(f"  note: {path} lacks {need - set(d.columns)}, skipping")
            continue
        d = d[list(need | {"category", "severity"} & set(d.columns))].copy()
        d["dR"] = d.R_opt - d.R_null
        frames.append(d)
    if not frames:
        sys.exit("no usable label sets found")
    return pd.concat(frames, ignore_index=True)


def fit_breakeven(dur, dR, boot, rng):
    """Least-squares zero-crossing of dR against duration, with a percentile
    bootstrap CI on D*. Returns (slope, D*, lo, hi, pearson_r)."""
    if len(dur) < 10:
        return (np.nan,) * 5
    slope, intercept = np.polyfit(dur, dR, 1)
    dstar = -intercept / slope if abs(slope) > 1e-15 else np.nan
    r = float(np.corrcoef(dur, dR)[0, 1])

    draws = np.empty(boot)
    n = len(dur)
    for b in range(boot):
        idx = rng.integers(0, n, n)
        s, i0 = np.polyfit(dur[idx], dR[idx], 1)
        draws[b] = -i0 / s if abs(s) > 1e-15 else np.nan
    draws = draws[np.isfinite(draws)]
    lo, hi = (np.percentile(draws, [2.5, 97.5]) if len(draws) > 100
              else (np.nan, np.nan))
    return slope, dstar, lo, hi, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=5000)
    ap.add_argument("--horizon", type=float, default=72.0)
    a = ap.parse_args()
    T = a.horizon
    rng = np.random.default_rng(0)

    d = load_labels()
    print(f"loaded {len(d)} option-scenario rows, "
          f"{d.option.nunique()} options, horizon T = {T:g} h\n")

    print("PROPOSITION 1: dR linear in D below the horizon, zero at D*")
    print("COROLLARY 1.1: dR flat above the horizon (saturation)\n")
    hdr = (f"{'option':>14} {'n<T':>5} {'D* (h)':>9} {'95% CI':>20} "
           f"{'r':>7} {'slope<T':>11} {'slope>=T':>11} {'Pr(D>D*)':>9}")
    print(hdr); print("-" * len(hdr))

    rows = []
    for opt in sorted(d.option.unique()):
        s = d[d.option == opt]
        below = s[s.duration_hr < T]
        above = s[s.duration_hr >= T]
        slope, dstar, lo, hi, r = fit_breakeven(
            below.duration_hr.to_numpy(), below.dR.to_numpy(), a.boot, rng)
        # saturation test: slope of the D >= T branch should be ~0
        if len(above) >= 10:
            sl_above = np.polyfit(above.duration_hr, above.dR, 1)[0]
        else:
            sl_above = np.nan
        p_exceed = float((s.duration_hr > dstar).mean()) if np.isfinite(dstar) else np.nan
        ci = f"[{lo:7.1f},{hi:8.1f}]" if np.isfinite(lo) else "        n/a        "
        print(f"{opt:>14} {len(below):5d} {dstar:9.1f} {ci:>20} {r:+7.3f} "
              f"{slope:+11.2e} {sl_above:+11.2e} {p_exceed:9.3f}")
        rows.append(dict(option=opt, D_star=dstar, ci_lo=lo, ci_hi=hi, r=r,
                         slope_below=slope, slope_above=sl_above,
                         p_exceed=p_exceed, n_below=len(below), n_above=len(above)))

    out = pd.DataFrame(rows)
    pathlib.Path("data").mkdir(exist_ok=True)
    out.to_csv("data/breakeven_estimates.csv", index=False)

    # --- saturation verdict (Corollary 1.1) ---
    print()
    ratio = (out.slope_above.abs() / out.slope_below.abs().replace(0, np.nan))
    med = float(np.nanmedian(ratio))
    print(f"SATURATION TEST: median |slope>=T| / |slope<T| = {med:.3f}")
    print("  Corollary 1.1 predicts this ratio near 0. Values close to 1 would "
          "falsify\n  the finite-horizon rescue-time model of Section 1.")

    # --- conditional vs unconditional partition ---
    cond = out[out.D_star > 0]
    unco = out[out.D_star <= 0]
    print(f"\nPARTITION: {len(unco)} unconditional options (D* <= 0), "
          f"{len(cond)} conditional (D* > 0)")
    if len(cond):
        print("  conditional options and their breakevens:")
        for _, rw in cond.sort_values("D_star").iterrows():
            print(f"    {rw.option:>14}  D* = {rw.D_star:6.1f} h   "
                  f"Pr(D > D*) = {rw.p_exceed:.3f}")
    print("\n  Corollary 2: an instantaneous-switching domain (tau -> 0) would "
          "place\n  every option in the unconditional partition. The conditional "
          "partition is\n  the signature of non-negligible transition time.")
    print("\nwrote data/breakeven_estimates.csv")


if __name__ == "__main__":
    main()
