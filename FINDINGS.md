# Findings Register — RDT Thesis III
Numbered, dated, commit-referenced. Every finding altered the model, the metric,
or the claim structure. This register feeds the thesis Methods/Discussion directly.

| # | Date | Finding | Number | Action | Commit |
|---|------|---------|--------|--------|--------|
| 1 | 07-03 | Eq. 2.11 scalar-incidence rank condition is vacuous (graph-theory identity) | rejects 0 of any topology | Degree/reachability filter; doc §2.4.1 amended v1.1 | 7f4bd17 |
| 2 | 07-03 | Carbonizer 573% loaded at dryer-limited feed; shell disposition required for steady ops | 45.9 vs 8 MT/day | YARD_SHELL→SNK_SHELL_SALE promoted to nominal | bfaaae6 |
| 3 | 07-03 | Mass-basis R blind to quality loss (oil↔meal mass-conserving) | D2 headroom 0.026→0.125 value-basis | Margin-weighted P(τ) made mandatory in Eq. 2.16 | 94187ba |
| 4 | 07-03 | Unbounded tank + uncapped V05 drawdown let static arm catch up unphysically | first paired ΔR −0.02→+0.048 after fix | I_max=50 t [est.], F_refine≤12 t/h | 94187ba |
| 5 | 07-03 | Reconfiguration value is decision-conditional; always-on destroys value in 75% of D3-refine | oracle +0.099 vs always-on +0.048; crossover 60 h (not naive 24 h) | GAT+MILP decision layer justified from data | 94187ba |
| 6 | 07-03 | Dryer holdup feed-scaled: outlet moisture feed-invariant (wrong physics) + 0/0 at Fs=0 | IDACalcIC fail @ sev 0.978 | Design-constant holdup (Fs_design=3,133 kg/h) | d41f350 |
| 7 | 07-03 | Wet route bypassed tank throttle → state parked on fmax kink → IC linesearch death | I_vco=49,833 vs I_max=50,000 | Wet line-up gated; C∞ tanh gate | d41f350 |
| 8 | 07-03 | D3-press zero-value row is CORRECT economics, not a gap: copra storable, catch-up 6× nominal, processing value ₱134/kg dominates sale ₱38/kg [est.] | R_null(press)≈0.98; max dR=0 across options | No copra_sale wiring; documented as self-buffering result | this |
| 9 | 07-03 | Scenario-identity collision (seed reused across categories) inflated decision-analysis oracle | 0.315 (wrong) vs 0.187 (true) | category+seed key; caught pre-claim | this |
| 10 | 07-03 | Impact labels are highly learnable from tabular features; GAT bar set | HistGBT CV R²=0.831±0.080, MAE 0.030 (σ=0.129); model-gated ΔR=0.178 = 95% of oracle 0.187, option-hit 81% | GAT claim (N2) reframed to what tabular CANNOT do: inductive generalization over graph structure / unseen topologies | this |

Standing implication of #10: H4 (ΔR≥0.15) is achievable by a LEARNED decision layer
with only 3 of 19 options wired (0.178 > 0.15 on D1/D3/D4/D8, n=160 scenarios).
The remaining option portfolio and D5/D6 raise the ceiling.
