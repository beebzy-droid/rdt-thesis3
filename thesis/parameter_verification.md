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

## Economic consequence, recomputed

`scripts/economics_verified.py` recomputes E11 under the verified parameters. As a
check on the recomputation, the as-modelled row reproduces the published figure of
PHP 100.7 M/yr exactly.

| Utility-outage frequency (siting) | phi = 0.30 (stress) | phi unconstrained | D4 share |
|---|---|---|---|
| as-modelled, 6.0/yr | 71.9 M | 100.7 M | 51% |
| urban, DLPC post-2017, 9.24/yr | 91.8 M | 128.7 M | 62% |
| urban, DLPC unplanned-only, 13.96/yr | 120.9 M | 169.4 M | 71% |
| cooperative, DORECO, 41.2/yr | 288.6 M | 404.7 M | 88% |
| cooperative, DANECO, 50.2/yr | 344.1 M | 482.4 M | 90% |

Verified phi is 0.63 or above, so the right-hand column is the defensible case and
the left is a stress test. Deliberately, no interpolation is performed between the
two phi points the campaign actually provides; two points do not determine a curve,
and a third invented number is exactly what the provenance ledger exists to prevent.

**The published economics are conservative by a factor of 1.3 for urban siting and
4.0 for cooperative siting.** That direction is the opposite of what a reader will
assume about an author's own economic estimate, and it should be stated rather than
left to be discovered.

### A fragility the larger number exposes

The utility-outage share of the total rises from 51% to 90% as the frequency moves
from the planning value to the cooperative case. A result in which nine tenths of
the benefit rests on a single parameter is fragile regardless of how well that
parameter is sourced, because any error in it passes through almost undamped. This
argues for reporting the siting cases as a band rather than promoting the largest,
and for treating the urban figure as the headline, since it is the most
conservative of the verified options.

### What the verification does not fix

Every peso figure scales linearly with V0, which depends on three prices that
remain unverified. The **ratios between rows do not depend on V0** and are the
defensible content of the table; the absolute levels remain indicative until the
PCA price series is obtained.

## Prices, closed at primary tier

Source documents: PCA Trade and Market Development Department, *Daily Market
Prices*, 31 July 2026; World Bank Commodity Price Data monthly series updated
2 July 2026; UCAP Weekly Bulletin Vol. LXVII No. 5, 2 February 2023.

| Parameter | Modelled | Observed | Direction |
|---|---|---|---|
| `w_copra_buy` | 40.0 | 47.94 Region XI farmgate (41.40 national) | conservative by 17% |
| `w_crude` | 140.0 | **100.8 to 125.44** domestic millgate | **optimistic by 12 to 39%** |
| `w_vco` | 200.0 | 204 derived implied export unit value | within 2% |

### The crude oil finding, and why it matters twice

This is the first parameter found to err in the unfavourable direction. The
modelled 140 PHP/kg corresponds not to crude coconut oil, quoted at 100.8 to
125.44, but to **refined RBD oil** at 132.72 to 143.36, which is a different
product from the crude stream the bypass option actually sells.

It matters a second time as a check on method. The earlier proxy took the World
Bank CIF Rotterdam series, converted it to roughly 141 PHP/kg, and observed that
it agreed with the modelled value to within one percent. The ledger recorded at
the time that this was a coincidence of basis rather than a validation, because
Rotterdam carries freight above domestic millgate. The primary figure now shows
the basis gap is 15 to 40 percent. **The apparent agreement was spurious, and the
caveat that prevented it from being reported as confirmation was doing real
work.** A proxy that agrees with a prior is the most dangerous kind, because
nothing prompts a second look.

### VCO: the earlier conclusion was half right

The previous entry recorded that no public VCO price exists. That was correct
about price series and wrong about derivability. No agency quotes a VCO price, but
UCAP reports export value and volume, and their ratio is an implied unit value of
3,490 USD/MT for October 2022, which is 204 PHP/kg at the period exchange rate
against a modelled 200. Since VCO output is overwhelmingly exported, FOB export
value is arguably the correct basis for the plant's realised price rather than a
substitute for it. The figure is one month and predates the current window, so it
confirms the order of magnitude rather than establishing a current price.

### Net economic effect is not a simple direction

Two parameters now push the economics up, utility-outage frequency and market
availability, and one pushes down, crude oil value. The product mix determines the
net, so the E11 recomputation should be rerun with all four before any revised
figure is quoted. Until then the previously reported range stands, with the
crude-oil correction noted as an offsetting term.

### Citation constraint

The UCAP Weekly Bulletin carries an explicit prohibition on reproducing its
articles or statistics without written consent. The two figures used here are
cited with attribution, which is ordinary academic practice for factual data, and
no UCAP table is reproduced. The PCA bulletin is a public government document and
itself credits UCAP as the source of its oil prices, so citing PCA is the cleaner
path where both carry the same figure.
