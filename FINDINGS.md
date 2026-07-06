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
| 11 | 07-03 | Graph→DAE compiler: topology is runtime data (§3.1.3 claim executable) | C1 equivalence 1.37e-14 all legacy topologies (⇒ 480 labels compiler-valid); compile+integrator 3.1 ms vs 40,000 ms §2.7 budget | Compiler is production path; legacy model demoted to reference | this |
| 12 | 07-03 | First multi-edge topology ΔG (solar train, +5 states, warm-start remap): full-yield capacity-limited solar vs full-throughput low-yield wet route trade | solar dR: D3 +0.092, D4 +0.195 (beats wet 0.185); 4-option oracle raises D3/D4 ceiling | Option-portfolio effects are real; labels carry n_edges_changed | this |
| 13 | 07-03 | Tabular baseline (finding #10) is ORACLE-INFORMED: it consumes duration_hr/severity — the disruption's FUTURE, unobservable at decision time. State-only graph snapshot (deployable info set) R²=0.623 vs oracle-tabular 0.868 on identical records/splits | ΔR² = 0.245 = measured value of disruption characterization (BOCPD + duration estimation); also exposes one-shot label framing as pessimistic — RDT loop re-decides every cycle (recurrent policy), reversible options change the calculus | H4 protocol note: recurrent policy evaluation; feature schema v1 to add trend channels; GAT bar restated as state-only 0.623, not 0.868 | this |
| 14 | 07-03 | GAT prototype (JAX, GATv2-faithful: edge-featured dynamic attention, ΔG edge channel, block-diagonal batching) at parity with flat state-only GBT on the FIXED option set | 5-fold R²=0.644±0.177 vs flat 0.623±0.159 (+0.021, within noise); seed-stable (fold-0: 0.636±0.007, n=3); MAE 0.043 | Expected per #10 reframing: fixed-set accuracy is not the GAT's claim. Decisive experiment queued: leave-one-option-out (LOTO) generalization to UNSEEN topology changes — the N2 test. Full 5-seed protocol deferred to PyG/reference GPU | this |
