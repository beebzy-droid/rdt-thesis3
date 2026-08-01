# Phase-5 Parameter Verification: First Results

*2026-07-13. Values extracted from the ERC reliability release and PSA OpenSTAT.
Every number below is traceable to a file and a computation; the extraction code
is `scripts/extract_parameters.py`.*

## Verified

| Parameter | Modeled | Observed | Source |
|---|---|---|---|
| `freq_D4` | 6.0 /yr | **9.4** urban, **41-50** cooperative | ERC SAIFI 2015-2023, Region XI |
| `buy_cap_frac_phi` | 0.30 | **0.63** direct strike, **0.88** peripheral, **~1.0** off-track | PSA production, derived |
| `w_nut` | 9.0 PHP/kg | **11.00** (24-mo mean, Davao) | PSA farmgate |

## Still unverified, and why

`w_copra_buy`, `w_crude`, `w_vco`. **PSA publishes whole-nut farmgate prices, not
copra.** Copra is the dried kernel, roughly a quarter of nut mass at four times the
value density, so the copra price cannot be read off the nut series without a
conversion that would itself be an assumption. These require the PCA price
monitoring series, which was not in the supplied data. They remain flagged.

## Two findings that change how results should be reported

**The economics are conservative, not optimistic.** This is the opposite of what a
reviewer will assume. The modeled outage frequency of 6/yr is below the best-served
urban utility in the region (9.4/yr recent era) and far below the cooperatives that
actually serve coconut-growing areas (DORECO 41.2, DANECO 50.2). Since `freq_D4`
carries 54% of the economic total, the reported figure understates the benefit by
a factor of roughly 1.6 for urban siting and up to 7 for cooperative siting. The
correct response is not to inflate the headline but to report the base case at
9.4/yr with a 6 to 50 band and to state that the value of the capability depends
strongly on where the plant sits, which is a result.

**Market availability is track-dependent, and this is the regional criterion made
observable.** The derived φ is 0.63 in a directly struck region (Eastern Visayas
after Yolanda), 0.88 in a peripherally struck one (Caraga after Odette), and
essentially 1.0 outside the track (Davao across both events). The theory predicted
that the value of reconfiguration depends on the regional disruption distribution;
here that dependence is visible in national statistics rather than assumed. The
modeled 0.3 is more pessimistic than any observed regional quarter, so the
φ-sensitivity result already reported is a genuine lower bound.

## Method, for reproduction

φ is the ratio of the first full quarter after landfall to the same quarter one
year earlier, in the affected region, using coconut-with-husk volume. The
one-year-lag denominator controls for the strong seasonal cycle in coconut
production. Davao serves as the off-track control for both events, and its ratios
near unity indicate the method is not simply detecting a national trend.

The `freq_D4` figures are total SAIFI summed across the ERC's four cause
categories (all-other, scheduled, power-supply, major-storm). Unplanned-only totals
excluding scheduled interruptions are also reported, since a scheduled outage is
not a disruption the twin must react to.
