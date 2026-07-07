"""scripts/analysis_prereg.py — PRE-REGISTERED analysis plan (lifecycle §5.4.3).

Committed BEFORE the full-scale campaign executes. Endpoints and tests are FROZEN
by this file's commit hash; any change after campaign data exists is a documented,
adviser-approved amendment (§9.2 no-silent-substitution rule).

ENDPOINTS (frozen):
  H4  primary   : pooled paired ΔR; bootstrap 95% CI (10,000 resamples).
                  PASS iff CI lower bound > 0.10; target-clear iff > 0.15.
                  Confirmation: Wilcoxon signed-rank, alpha = 0.05.
  H5  secondary : TTR80 relative reduction on episodes impaired under static;
                  PASS iff CI lower bound > 0.20; target-clear iff > 0.30.
                  NOTE: static-arm TTR80 not collected by campaign.py v1 —
                  H5 here reports RDT-arm TTR distribution + never-impaired and
                  no-recovery fractions; paired H5 requires static TTR (amendment
                  A1 candidate, flagged pre-campaign).
  E9  gate      : harm fraction P(ΔR < −0.01) reported per category; deployability
                  discussion threshold 5% pooled.
  Plausibility  : switches median <= 12 per episode.
  Dose-response : ΔR vs severity deciles per category (RQ4 curve).
  E11 economics : PHP translation, parameters below — every price [est.]/[verify].

Usage: python scripts/analysis_prereg.py
"""
import sys, pathlib, glob
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

# ---- E11 parameters: ALL [est.; verify PCA price monitors + PAGASA/plant records
#      before manuscript use; ±30% sensitivity mandated] ----
V0_PHP_HR = None          # computed from data if present, else steady-state calc
R_WINDOW_HR = 72.0
EPISODES_PER_YR = {"D1": 2.0, "D3": 4.0, "D4": 6.0, "D8": 1.0}   # [est.; verify]
PRICE_SENS = 0.30

BOOT = 10_000
RNG = np.random.default_rng(20260703)


def ci(x, stat=np.mean):
    bs = np.array([stat(RNG.choice(x, len(x))) for _ in range(BOOT)])
    return stat(x), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


def main():
    files = sorted(glob.glob("data/campaign/*.parquet"))
    if not files:
        print("no campaign shards found — run scripts/campaign.py first"); return
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    n = len(df)
    print(f"campaign shards: {len(files)} | paired scenarios: {n}")

    # ---------- H4 ----------
    m, lo, hi = ci(df.dR.to_numpy())
    w = wilcoxon(df.dR).pvalue
    print(f"\nH4 pooled ΔR = {m:.4f}, 95% CI [{lo:.4f}, {hi:.4f}] | "
          f"formal PASS (CI>0.10): {lo > 0.10} | target (CI>0.15): {lo > 0.15} | "
          f"Wilcoxon p = {w:.2e}")
    g = df.groupby("category").agg(n=("dR", "size"), R_static=("R_static", "mean"),
        R_rdt=("R_rdt", "mean"), dR=("dR", "mean"),
        dR_p5=("dR", lambda s: s.quantile(.05)),
        harm=("dR", lambda s: (s < -0.01).mean()),
        sw_med=("n_switches", "median"),
        det_miss=("det_delay", lambda s: s.isna().mean()),
        det_med_hr=("det_delay", "median"),
        degraded_mean=("degraded", "mean"))
    print(g.round(3).to_string())

    # ---------- plausibility + E9 ----------
    print(f"\nE9 harm pooled: {(df.dR < -0.01).mean():.1%} (discussion threshold 5%) | "
          f"switches median: {df.n_switches.median():.0f} (gate <= 12)")

    # ---------- H5 (RDT-arm distribution; paired pending amendment A1) ----------
    print(f"H5 (RDT arm): TTR80 never-impaired {(df.TTR_rdt == 0).mean():.0%}, "
          f"no-recovery {(df.TTR_rdt.isna()).mean():.0%}, "
          f"impaired median {df.TTR_rdt[df.TTR_rdt > 0].median():.1f} h")

    # ---------- dose-response (RQ4) ----------
    df["sev_dec"] = pd.qcut(df.severity, 5, labels=False, duplicates="drop")
    dr = df.pivot_table(index="sev_dec", columns="category", values="dR")
    print("\nΔR dose-response by severity quintile:")
    print(dr.round(3).to_string())

    # ---------- E11 ----------
    v0 = V0_PHP_HR or 470_000.0     # PHP/hr nominal value flow [est.; from model]
    print(f"\nE11 [ALL PRICES est./verify]: V0 ≈ ₱{v0:,.0f}/hr")
    per_cat = df.groupby("category").dR.mean()
    php_ep = per_cat * R_WINDOW_HR * v0
    php_yr = sum(php_ep[c] * EPISODES_PER_YR.get(c, 0) for c in php_ep.index)
    for c in php_ep.index:
        print(f"  {c}: avoided loss ₱{php_ep[c]/1e6:.2f} M/episode × "
              f"{EPISODES_PER_YR.get(c, 0)}/yr [est.]")
    print(f"  annualized benefit ≈ ₱{php_yr/1e6:.1f} M/yr "
          f"(±30% price sens: ₱{php_yr*(1-PRICE_SENS)/1e6:.1f}–"
          f"₱{php_yr*(1+PRICE_SENS)/1e6:.1f} M/yr)")


if __name__ == "__main__":
    main()
