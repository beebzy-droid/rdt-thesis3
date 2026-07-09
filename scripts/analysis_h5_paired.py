"""scripts/analysis_h5_paired.py — Amendment A1 adjudication (frozen H5 endpoint).

Joins campaign v1 shards (RDT arm TTR) with A1 supplement shards (static arm TTR,
identical seeds) and adjudicates:
  H5: relative TTR80 reduction on episodes IMPAIRED under static (TTR_static > 0,
      both arms finite). PASS iff bootstrap 95% CI lower bound > 0.20;
      target-clear iff > 0.30. (Endpoint text unchanged from analysis_prereg.py.)
  NaN-asymmetry table: static-no-recovery vs RDT outcome (reduction undefined there;
      reported as counts — these episodes FAVOR the RDT and are excluded from the
      ratio, making the H5 number conservative).
  INTEGRITY GATE: R_static(A1) must match R_static(campaign) to < 1e-9 per scenario —
      a mismatch means shard corruption or code drift between runs; adjudication
      REFUSES to proceed on mismatch (§9.2).
"""
import sys, glob, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401  (force UTF-8 stdout)
import numpy as np
import pandas as pd

BOOT = 10_000
RNG = np.random.default_rng(20260704)


def load(pattern):
    files = sorted(glob.glob(pattern))
    if not files:
        sys.exit(f"no shards match {pattern}")
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def main():
    camp = load("data/campaign/*.parquet")
    a1 = load("data/campaign_a1/*.parquet")
    # v1/v1.1 skew guard: campaign v1.1 shards carry TTR_static natively; the A1
    # supplement is the declared source of truth for static TTR — drop the native
    # column pre-merge so both shard generations adjudicate identically
    camp = camp.drop(columns=["TTR_static"], errors="ignore")
    m = camp.merge(a1, on=["category", "seed"], how="inner")
    print(f"joined scenarios: {len(m)} (campaign {len(camp)}, a1 {len(a1)})")

    # ---- integrity gate ----
    dev = (m.R_static - m.R_static_a1).abs().max()
    print(f"integrity: max |R_static(campaign) − R_static(A1)| = {dev:.2e}")
    if dev > 1e-9:
        sys.exit("INTEGRITY GATE FAIL — shard mismatch; do not adjudicate (§9.2)")

    # ---- H5 paired, frozen endpoint ----
    both = m[(m.TTR_static > 0) & np.isfinite(m.TTR_static) & np.isfinite(m.TTR_rdt)]
    red = (1 - both.TTR_rdt / both.TTR_static).to_numpy()
    bs = np.array([RNG.choice(red, len(red)).mean() for _ in range(BOOT)])
    lo, hi = np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    print(f"\nH5 paired (n={len(red)} impaired-under-static, both finite):")
    print(f"  mean TTR80 reduction = {red.mean():.1%}, 95% CI [{lo:.1%}, {hi:.1%}]")
    print(f"  PASS (CI>20%): {lo > 0.20} | target (CI>30%): {lo > 0.30}")
    g = both.groupby("category").apply(
        lambda d: pd.Series({"n": len(d),
                             "red_mean": (1 - d.TTR_rdt / d.TTR_static).mean(),
                             "TTR_s_med": d.TTR_static.median(),
                             "TTR_r_med": d.TTR_rdt.median()}), include_groups=False)
    print(g.round(3).to_string())

    # ---- NaN asymmetry (conservatism accounting) ----
    s_nr = m.TTR_static.isna()
    r_nr = m.TTR_rdt.isna()
    print("\nno-recovery asymmetry (excluded from ratio — favors RDT):")
    print(f"  static no-recovery & RDT recovers: {int((s_nr & ~r_nr).sum())}")
    print(f"  static no-recovery & RDT no-recovery: {int((s_nr & r_nr).sum())}")
    print(f"  static recovers & RDT no-recovery: {int((~s_nr & r_nr).sum())}  <- adverse")
    print(f"  static never-impaired {int((m.TTR_static == 0).sum())} vs "
          f"RDT never-impaired {int((m.TTR_rdt == 0).sum())}")


if __name__ == "__main__":
    main()
