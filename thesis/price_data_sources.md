# Obtaining Philippine Coconut Price Data

*2026-07-13. Written after establishing that one of the three prices the economics
depend on cannot be obtained from any free public source. Recorded so the next
person does not repeat the search.*

## The trap to avoid first

PSA OpenSTAT publishes **"Coconut Mature"** and **"Coconut Young"** farmgate
prices. These are **whole nuts**, not copra. Copra is the dried kernel, roughly
four to six nuts per kilogram, and trades at several times the value density. A
study that reads copra economics off the OpenSTAT coconut line is wrong by a large
factor and will look, to anyone in the sector, like the author did not know the
commodity. This is the single most common error for this task and it is easy to
make, because the series is well maintained and sits exactly where a copra price
ought to be.

## Copra: available

**Primary.** Philippine Coconut Authority, Commodity Price Watch. From
`pca.gov.ph`, follow **Trade & Market → Commodity Price Watch**. Gives daily and
monthly farmgate and millgate copra in PHP/kg with regional breakdown, which is
the only source offering Davao and Mindanao granularity. The annual **Coconut
Statistics** PDF under Resources carries province-level price tables.

Expect friction. The site runs bot detection that blocks automated fetching, and
it goes down periodically. Fallbacks are the PCA Facebook page, which posts current
prices, and an FOI request at `foi.gov.ph/agencies/pca` for historical series.

**Free re-publication.** The International Coconut Community publishes a weekly
price update at `coconutcommunity.org` under Market & Statistics, with monthly PDF
archives back to 2016 at a predictable URL pattern. Its own notes state that the
Philippine figures come from PCA and UCAP, so this is the same data without the
website friction, in USD/MT rather than PHP/kg. Philippine copra is quoted "not
quoted" on thin trading weeks, so expect gaps.

**Paid.** UCAP sells a daily market report and weekly bulletin at roughly USD 250
per year each. Authoritative, and unnecessary if the ICC re-publication suffices.

**Grade matters.** Copra is graded by moisture. *Resecada* is well dried at about
5 to 6 percent; *corriente* is ordinary at 14 percent and above. Since PCA
Administrative Order No. 01 of 1991 the base price is set at 12 percent moisture,
called semi-resecada, with adjustments across the 12 to 7 percent range. Mixing
grades corrupts a series, so record which basis a quote uses.

## Crude coconut oil: available

**International benchmark.** World Bank Commodity Price Data, the "Pink Sheet".
From `worldbank.org/commodities`, download the monthly prices XLSX. The line is
"Coconut oil", Philippines/Indonesia, crude, CIF Rotterdam, in USD per metric
tonne, monthly back to 1960. Free, no registration, updated in the first week of
each month.

**The basis caveat that matters.** CIF Rotterdam includes freight and sits
structurally above Philippine domestic millgate. Converting it to PHP/kg gives a
number that looks like a domestic price and is not one. For a domestic millgate
series on a consistent basis, use the ICC weekly update, which carries
"Philippines (Domestic, Millgate Price)" alongside the Rotterdam quote.

**Aggregators.** IndexMundi and similar sites republish the World Bank series with
convenient charts. They are re-publications, can lag by a month, and occasionally
mislabel units. Cite the World Bank XLSX, not the aggregator.

## Virgin coconut oil: not available

This is the finding, and it should be stated rather than worked around.

VCO appears in no free public price series. It is absent from PSA OpenSTAT, from
the PCA Commodity Price Watch, and from DA Bantay Presyo, which covers retail food
commodities only. Internationally, VCO has no unique six-digit HS code and falls
under 1513.11, crude coconut oil. The Philippines defines a national eleven-digit
line, PSCC 1513.11.10-009, with sub-codes by extraction process, but it is not
disseminated as a labelled public series, and PSA trade tables aggregate crude,
refined and virgin oil into one "Coconut Oil" line. An FOI request on this point
returned only the aggregate tables.

Three honest routes remain. Buy a UCAP subscription or a trade-data vendor feed.
File a PSA Trade Statistics microdata request for the eleven-digit line, accepting
that it may be returned only at the aggregate level. Or use a documented premium
multiple over verified crude coconut oil and state it as an assumption. Historic
anchors exist, 4,348 USD/mt FOB Manila in 2015 and 2,522 in 2017, but they are
stale and cannot serve as a series.

## Conversions, for deriving one price from another

Dry copra yields roughly 0.61 to 0.68 kilograms of oil per kilogram, with about
0.37 kilograms of meal sold separately. Roughly five thousand nuts make a tonne of
copra. The price ordering runs whole nut, copra, crude coconut oil, refined oil,
virgin oil.

A naive division of copra price by oil yield overstates raw-material cost, because
it ignores the meal credit. If a derivation is unavoidable, state the yield, the
meal credit, and the margin assumption separately so a reader can vary each.

## Recommended order

Take crude coconut oil first, since one World Bank download settles it. Take copra
second, from ICC for a quick series and from PCA when regional granularity is
needed. Leave virgin coconut oil last and expect to record it as an assumption.
