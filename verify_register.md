# Verification Register — Phase-5 worklist

Derived from `provenance.yaml`. Ordered by economic leverage. A row closes when its
`provenance.yaml` entry gets a real citation in `source` and `verified: true`;
`python scripts/check_provenance.py` then reflects it. **No manuscript number may
cite an open row** (§9.2). Run `check_provenance.py --strict` as the manuscript gate.

## Tier 1 — E11-critical (blocks the economic claim)

| # | Parameter | Value | Source to obtain | Why it matters |
|---|---|---|---|---|
| 1 | **freq_D4** | 6 /yr | DOE / NGCP interruption indices (SAIFI), CALABARZON | **54% of the uncapped ₱100.7M/yr** — single highest-leverage number in the thesis |
| 2 | buy_cap_frac φ | 0.3 | PCA trader survey / post-disaster copra market depth | Moves pooled H4 0.244→0.174 and E11 by 14%; the φ-curve's x-axis |
| 3 | w_vco | 200 ₱/kg | PCA / DA Bantay-Presyo VCO monitor | Highest product weight in the value basis |
| 4 | w_copra_buy | 40 ₱/kg | PCA copra farmgate monitor | Dominant D1/D8 rescue value + φ economics |
| 5 | w_crude | 140 ₱/kg | PCA crude CNO series | crude_bypass option value |

## Tier 2 — ΔR-shaping (affects effect size, not the annualization)

| # | Parameter | Value | Source |
|---|---|---|---|
| 6 | freq_D1 | 2 /yr | PAGASA cyclone climatology, sourcing-region landfalls |
| 7 | freq_D3 | 4 /yr | plant reliability / agro-processing MTBF (Phase-5 interviews) |
| 8 | nut_mass | 1.2 kg | PSA regional whole-nut mass — scales absolute throughput → E11 linearly |
| 9 | y_oil / y_wet | 0.63 / 0.30 | cold-press assay; wet-route penalty |
| 10 | f_kernel…f_water | 0.30/0.15/0.35/0.20 | processing literature + plant assay |
| 11 | w_meal / w_conc | 22 / 100 ₱/kg | feed millers (PSA) / concentrate export price |

## Tier 3 — pure ASSUMPTIONS (no source exists; state as such or replace)

| # | Parameter | Value | Note |
|---|---|---|---|
| 12 | w_copra_sale | 38 ₱/kg | buy − 2 spread; replace with real bid-ask if available |
| 13 | w_fuel_offset | 12 ₱/kg | shell fuel vs 8 sale; low weight |
| 14 | D3 failure weights | uniform | plant MTBF by unit would refine |

## Modeling follow-on (not a parameter lookup)
- **φ(severity) correlation** — the inverted-U in F#25/§6.6 requires availability that
  falls with disruption severity, not a constant φ. This is a scenario-model change
  (couple buy_cap_frac to the D1/D8 severity draw), not a single number to verify.
