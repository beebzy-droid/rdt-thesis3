"""scripts/economics_verified.py — E11 under source-verified parameters.

Recomputes the annualized economic benefit using the values verified in
thesis/parameter_verification.md, and reports how far the previously published
figure sat from the observed evidence.

Two parameters moved, and both moved in the same direction:

  freq_D4  planning value 6.0/yr. ERC 2015-2023 SAIFI for Region XI gives 9.24/yr
           for the best-served urban utility post-2017 and 41-50/yr for the rural
           cooperatives that serve coconut-growing areas. Because utility outage
           carries the largest single share of E11, this is the dominant term.

  phi      planning value 0.30. Derived from PSA production records, the observed
           post-landfall availability is 0.63 in a directly struck region and 0.88
           in a peripherally struck one. Every observed regional quarter is less
           severe than the modeled stress case.

DELIBERATE RESTRAINT ON phi. The campaign gives pooled dR at exactly two points,
phi = 0.3 (0.1739) and uncapped (0.2438). Verified phi lies at 0.63 or above, so
the true value lies between them and nearer the uncapped end. We do NOT
interpolate: two points do not determine the curve, and inventing a third would be
exactly the kind of unearned precision the provenance ledger exists to prevent.
Both bounds are reported and the reader is told which is conservative.

Usage: python scripts/economics_verified.py
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from rdt_core import _console  # noqa: F401

# ---- audited campaign constants (frozen; see thesis/results_chapter.md) ----
R_WINDOW_HR = 72.0
V0_PHP_HR = 470_000.0            # [est.] nominal value flow; still unverified
PRICE_SENS = 0.30

DR_UNCAPPED = {"D1": 0.306, "D3": 0.140, "D4": 0.255, "D8": 0.275}
DR_POOLED_UNCAPPED = 0.2438
DR_POOLED_PHI03 = 0.1739
PHI03_SCALE = DR_POOLED_PHI03 / DR_POOLED_UNCAPPED   # 0.713, applied per category

# ---- frequencies ----
FREQ_PLANNING = {"D1": 2.0, "D3": 4.0, "D4": 6.0, "D8": 1.0}
# Verified freq_D4 by siting (ERC SAIFI, Region XI, total across cause classes)
FREQ_D4_SITING = {
    "as-modelled (planning)":        6.00,
    "urban, DLPC post-2017":         9.24,
    "urban, DLPC unplanned-only":   13.96,
    "cooperative, DORECO":          41.22,
    "cooperative, DANECO":          50.23,
}


def annual(dr_map, freq_d4, v0=V0_PHP_HR):
    freq = dict(FREQ_PLANNING, D4=freq_d4)
    per_ep = {c: dr_map[c] * R_WINDOW_HR * v0 for c in dr_map}
    total = sum(per_ep[c] * freq[c] for c in per_ep)
    d4_share = per_ep["D4"] * freq["D4"] / total if total else float("nan")
    return total, d4_share


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v0", type=float, default=V0_PHP_HR)
    a = ap.parse_args()

    dr_phi03 = {c: v * PHI03_SCALE for c, v in DR_UNCAPPED.items()}

    print("E11 UNDER SOURCE-VERIFIED PARAMETERS")
    print(f"V0 = PHP {a.v0:,.0f}/hr [STILL UNVERIFIED: prices need PCA series]\n")
    print("Rows: utility-outage frequency, ERC SAIFI Region XI by siting.")
    print("Columns: market availability. Verified phi is 0.63 or above, so the")
    print("right-hand column is the defensible case and the left is a stress test.\n")

    hdr = f"{'siting (freq_D4)':<30}{'phi=0.30 (stress)':>20}{'phi unconstrained':>20}{'D4 share':>11}"
    print(hdr); print("-" * len(hdr))
    base = None
    for label, f4 in FREQ_D4_SITING.items():
        lo, _ = annual(dr_phi03, f4, a.v0)
        hi, share = annual(DR_UNCAPPED, f4, a.v0)
        if base is None:
            base = hi
        print(f"{label:<30}{lo/1e6:>16.1f} M {hi/1e6:>16.1f} M {share:>10.0%}")

    print("\nHOW FAR THE PUBLISHED FIGURE SITS FROM THE EVIDENCE")
    pub_lo, _ = annual(dr_phi03, 6.0, a.v0)
    pub_hi, _ = annual(DR_UNCAPPED, 6.0, a.v0)
    print(f"  published range, planning parameters      "
          f"PHP {pub_lo/1e6:.1f} to {pub_hi/1e6:.1f} M/yr")
    for label in ("urban, DLPC post-2017", "cooperative, DORECO"):
        f4 = FREQ_D4_SITING[label]
        v_hi, _ = annual(DR_UNCAPPED, f4, a.v0)
        print(f"  {label:<40} PHP {v_hi/1e6:.1f} M/yr "
              f"({v_hi/pub_hi:.2f}x the published upper figure)")

    print("\n  Both verified parameters move the result UPWARD. The published")
    print("  economics are therefore conservative rather than optimistic, which")
    print("  is the opposite of the direction a reviewer will assume, and it")
    print("  should be stated plainly rather than left to be discovered.")

    print("\nWHAT IS STILL UNVERIFIED, and why the absolute figures stay indicative")
    print("  V0 depends on w_vco, w_crude and w_copra_buy, none of which can be")
    print("  read from the PSA farmgate series, because PSA publishes WHOLE NUT")
    print("  prices while copra is the dried kernel at roughly four times the")
    print("  value density. Until the PCA price series is obtained, every peso")
    print("  figure above scales linearly with an unverified V0 and must be")
    print("  reported as indicative. The RATIOS between rows do not depend on V0")
    print("  and are the defensible content of this table.")

    print(f"\n  Price sensitivity as previously reported: +/-{PRICE_SENS:.0%} on V0.")


if __name__ == "__main__":
    main()
