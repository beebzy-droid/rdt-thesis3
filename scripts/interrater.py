"""scripts/interrater.py — inter-rater agreement for the evaluation-practice audit.

Computes Cohen's kappa per protocol and overall between two independent raters
scoring published evaluations against the six protocols (see audit/rubric.md).

Kappa rather than raw agreement, because several protocols have a dominant code
(P6 is NA almost everywhere, P2 is NR almost everywhere) and raw agreement would
be flattered by chance alone. Kappa corrects for that, and where a protocol is
degenerate (one code used for every paper by both raters) kappa is undefined and
is reported as such rather than as zero or one.

A bootstrap interval over papers is reported because the sample is small; a point
estimate of kappa on seven papers would overstate what has been established.

Usage:
    python scripts/interrater.py
    python scripts/interrater.py --r1 audit/scores_rater1_SEALED.csv \
                                 --r2 audit/scores_rater2.csv --boot 10000
"""
import argparse
import itertools
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401

import numpy as np
import pandas as pd

PROTOCOLS = ["P1", "P2", "P3", "P4", "P5", "P6"]


def cohen_kappa(a, b):
    """Cohen's kappa for two equal-length code sequences. Returns nan when the
    rating is degenerate (both raters used a single identical code throughout),
    because agreement carries no information in that case."""
    a, b = np.asarray(a, dtype=object), np.asarray(b, dtype=object)
    codes = sorted(set(a) | set(b))
    if len(codes) < 2:
        return np.nan
    idx = {c: i for i, c in enumerate(codes)}
    n = len(a)
    m = np.zeros((len(codes), len(codes)))
    for x, y in zip(a, b):
        m[idx[x], idx[y]] += 1
    po = np.trace(m) / n
    pe = float((m.sum(0) * m.sum(1)).sum()) / (n * n)
    if abs(1.0 - pe) < 1e-12:
        return np.nan
    return (po - pe) / (1.0 - pe)


def boot_ci(a, b, boot, rng):
    n = len(a)
    if n < 3:
        return np.nan, np.nan
    draws = []
    for _ in range(boot):
        i = rng.integers(0, n, n)
        k = cohen_kappa(np.asarray(a)[i], np.asarray(b)[i])
        if np.isfinite(k):
            draws.append(k)
    if len(draws) < 50:
        return np.nan, np.nan
    return float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r1", default="audit/scores_rater1_SEALED.csv")
    ap.add_argument("--r2", default="audit/scores_rater2.csv")
    ap.add_argument("--boot", type=int, default=10000)
    a = ap.parse_args()

    p2 = pathlib.Path(a.r2)
    if not p2.exists():
        print(f"second rating not found at {a.r2}.")
        print("\nProtocol (audit/README.md):")
        print("  1. score audit/scoring_sheet_BLANK.csv using audit/rubric.md")
        print("  2. save as audit/scores_rater2.csv")
        print("  3. only then open audit/scores_rater1_SEALED.csv")
        print("  4. re-run this script")
        sys.exit(0)

    # keep_default_na=False is essential: the code "NA" (not applicable) is a
    # valid score, and pandas would otherwise read it as a missing value and
    # silently corrupt every P6 column, which is NA almost everywhere.
    r1 = pd.read_csv(a.r1, keep_default_na=False).set_index("paper_id")
    r2 = pd.read_csv(p2, keep_default_na=False).set_index("paper_id")
    shared = [i for i in r1.index if i in r2.index]
    if not shared:
        sys.exit("no shared paper_id values between the two ratings")
    print(f"{len(shared)} papers scored by both raters\n")

    rng = np.random.default_rng(0)
    hdr = f"{'protocol':>9} {'kappa':>8} {'95% CI':>18} {'agree':>7} {'codes used':>22}"
    print(hdr); print("-" * len(hdr))
    kappas, all1, all2 = [], [], []
    for pr in PROTOCOLS:
        x = [str(r1.loc[i, pr]).strip() for i in shared]
        y = [str(r2.loc[i, pr]).strip() for i in shared]
        all1 += x; all2 += y
        k = cohen_kappa(x, y)
        lo, hi = boot_ci(x, y, a.boot, rng)
        agree = float(np.mean([u == v for u, v in zip(x, y)]))
        used = ",".join(sorted(set(x) | set(y)))
        ci = f"[{lo:6.2f},{hi:6.2f}]" if np.isfinite(lo) else "       n/a       "
        kstr = f"{k:8.3f}" if np.isfinite(k) else "  degen."
        print(f"{pr:>9} {kstr} {ci:>18} {agree:7.2f} {used:>22}")
        if np.isfinite(k):
            kappas.append(k)

    k_all = cohen_kappa(all1, all2)
    lo, hi = boot_ci(all1, all2, a.boot, rng)
    print("-" * len(hdr))
    agree_all = float(np.mean([u == v for u, v in zip(all1, all2)]))
    ci = f"[{lo:6.2f},{hi:6.2f}]" if np.isfinite(lo) else "       n/a       "
    print(f"{'POOLED':>9} {k_all:8.3f} {ci:>18} {agree_all:7.2f}")
    if kappas:
        print(f"{'mean-of-6':>9} {np.mean(kappas):8.3f}")

    # ---- disagreement report: what to resolve ----
    print("\nDISAGREEMENTS to resolve by discussion")
    rows = []
    for i in shared:
        for pr in PROTOCOLS:
            u, v = str(r1.loc[i, pr]).strip(), str(r2.loc[i, pr]).strip()
            if u != v:
                conf = r1.loc[i, "confidence"] if "confidence" in r1.columns else "?"
                rows.append((i, pr, u, v, conf))
    if not rows:
        print("  none")
    else:
        print(f"{'paper':>6} {'proto':>6} {'rater1':>7} {'rater2':>7} {'r1 conf':>8}")
        for i, pr, u, v, c in rows:
            print(f"{i:>6} {pr:>6} {u:>7} {v:>7} {c:>8}")
        print(f"\n  {len(rows)} of {len(shared)*len(PROTOCOLS)} cells disagree.")
        print("  Where rater 1's confidence is medium, the presumption favours")
        print("  rater 2, who read the full text (audit/README.md).")

    print("\nReport BOTH the pre-resolution kappa above and the post-resolution")
    print("consensus scores. Kappa below about 0.4 indicates the rubric is not")
    print("operational enough to publish and should be revised first.")


if __name__ == "__main__":
    main()
