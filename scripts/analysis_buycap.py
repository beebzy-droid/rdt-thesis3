"""scripts/analysis_buycap.py — Finding #25 sensitivity adjudication.

Compares D1/D8 under buy_cap_frac=0.3 [est.] against the uncapped campaign on
identical seeds. Outputs (manuscript rule: D1/D8 ΔR reported as f(φ), never scalar):
  per-category ΔR at φ=0.3 vs uncapped, paired per-scenario deltas
  severity-quintile dose-response at φ=0.3 (does the inverted-U appear?)
  REVISED pooled H4: D1/D8 rows replaced by φ=0.3 values, D3/D4 unchanged
  REVISED E11 under φ=0.3
"""
import sys, glob, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np
import pandas as pd

BOOT = 10_000
RNG = np.random.default_rng(20260704)
V0, W = 470_000.0, 72.0
FREQ = {"D1": 2.0, "D3": 4.0, "D4": 6.0, "D8": 1.0}   # [est.; verify]


def load(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        sys.exit(f"no shards match {pattern}")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def ci(x):
    bs = np.array([RNG.choice(x, len(x)).mean() for _ in range(BOOT)])
    return x.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def main():
    unc = load("data/campaign/*.parquet")
    cap = load("data/campaign_cap0.3/*.parquet")
    j = unc.merge(cap, on=["category", "seed"], suffixes=("_unc", "_cap"))
    print(f"paired scenarios (uncapped x φ=0.3): {len(j)}")

    g = j.groupby("category").agg(
        dR_uncapped=("dR_unc", "mean"), dR_cap03=("dR_cap", "mean"),
        delta=("dR_cap", "mean"))
    g["delta"] = g.dR_cap03 - g.dR_uncapped
    print(g.round(3).to_string())

    j["sev_q"] = j.groupby("category").severity_unc.transform(
        lambda s: pd.qcut(s, 5, labels=False, duplicates="drop"))
    dr = j.pivot_table(index="sev_q", columns="category", values="dR_cap")
    print("\nΔR dose-response at φ=0.3 (inverted-U check):")
    print(dr.round(3).to_string())

    # revised pooled H4 under φ=0.3 for D1/D8
    full = load("data/campaign/*.parquet")
    repl = pd.concat([full[~full.category.isin(cap.category.unique())],
                      cap], ignore_index=True)
    m, lo, hi = ci(repl.dR.to_numpy())
    print(f"\nREVISED pooled H4 @ φ=0.3: ΔR = {m:.4f}, CI [{lo:.4f}, {hi:.4f}] | "
          f"formal (>0.10): {lo > 0.10} | target (>0.15): {lo > 0.15}")

    php = 0.0
    for c, grp in repl.groupby("category"):
        php += grp.dR.mean() * W * V0 * FREQ.get(c, 0)
    print(f"REVISED E11 @ φ=0.3: ≈ ₱{php/1e6:.1f} M/yr "
          f"(±30%: {php*0.7/1e6:.1f}–{php*1.3/1e6:.1f}) [all est./verify]")


if __name__ == "__main__":
    main()
