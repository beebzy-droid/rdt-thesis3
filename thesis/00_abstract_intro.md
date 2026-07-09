# Reactive Digital Twin with Graph-Guided Topology Reconfiguration and MILP Optimization for Resilient Philippine Coconut Processing Complex Operations Under Supply Chain Disruption

*Thesis draft — front matter + Chapter 1. v1, 2026-07-04. Companion to Chapter 6
(Results) and Chapter 7 (Discussion). All quantitative claims trace to FINDINGS.md
(F#n); [est.]/[verify] flags mark parameters pending Phase-5 verification (§9.2).*

---

## ABSTRACT

Every published digital twin in chemical process engineering treats plant
topology — the network of pipes, unit routings, and utility connections — as a
fixed structure. This assumption fails precisely when it matters most: during a
supply-chain disruption, when the physical plant must reroute streams, bypass
units, and re-prioritize products, and a topology-frozen twin can neither
represent nor prescribe the response. This thesis develops the first **Reactive
Digital Twin (RDT)**: a digital twin that reconfigures its own process-network
topology in real time. The RDT couples four engines — Bayesian online change-point
detection, a learned feasibility/impact screen over candidate reconfigurations,
a mixed-integer linear program that selects and sequences changes, and a
differential-algebraic plant model that verifies the transition — in a recurrent
decision loop.

The framework is validated on a physics-based model of an integrated Philippine
coconut processing complex (virgin coconut oil, copra meal, shell charcoal,
coconut water concentrate; seven unit operations, four utility networks) under
typhoon-calibrated disruption scenarios. Across a pre-registered campaign of 2,000
paired Monte-Carlo runs with common random numbers, the RDT improves the
72-hour resilience integral by **ΔR = 0.244 (95% CI [0.237, 0.251])** against a
strong static comparator, remaining above the 0.15 target even under a
pessimistic purchased-input market assumption (**ΔR = 0.174 [0.168, 0.180]**),
and reduces time-to-80%-recovery by **57.7% [55.2, 60.2]**. The economic
translation is **₱86–101 million per year** [est.] of avoided lost production for
a reference-scale complex, at a simple payback under two months against
indicative deployment cost.

Three results generalize beyond the case study. First, the value of every
resilience decision — which reconfiguration, informed by what, and how
aggressively to deploy inventory — is *disruption-conditional*, and a recurrent
loop applying imperfect information repeatedly outperforms one-shot perfect
foresight. Second, evaluating adaptive systems demands comparator *symmetry*, not
merely comparator strength: an asymmetric strong baseline produced a formal false
negative that symmetric arms reversed. Third, learned graph-attention screening
of topology changes does not generalize to unseen reconfigurations at the data
scale reachable here — a documented negative that the layered architecture
renders non-blocking. The complete framework, simulation, disruption library, and
analysis pipeline are released as open source with a one-command reproducibility
harness.

**Keywords:** digital twin; process network reconfiguration; graph neural
networks; mixed-integer programming; resilience; supply-chain disruption;
coconut processing; Philippines.

---

# CHAPTER 1 — INTRODUCTION

## 1.1 The problem: twins that cannot follow their plants

A digital twin is a virtual replica synchronized with a physical asset, used to
monitor, predict, and increasingly to prescribe. In chemical process engineering
the concept has matured through monitoring and predictive tiers toward
prescriptive twins that couple a plant model to an optimizer. Yet across this
literature one object is held constant: the *topology* of the process network.
The optimizer may manipulate setpoints, splits, and utility loads, but the graph
connecting the units — which stream feeds which vessel, which bypass exists,
which product route is open — is compiled into the model at build time and does
not change.

This rigidity is invisible during normal operation and catastrophic during
disruption. When a typhoon interrupts feedstock supply, a utility header fails,
or a unit is isolated for unplanned maintenance, the physical plant survives by
*reconfiguring*: rerouting partially processed material, switching fuel sources,
bypassing lost capacity, shifting the product slate. A topology-frozen twin
cannot represent the reconfigured plant, cannot compute recovery trajectories
through it, and therefore delivers zero prescriptive value in exactly the window
— the first minutes to hours after onset — where routing decisions determine
whether throughput recovers in days or weeks. The twin is most useful when least
able to help.

## 1.2 The setting: Philippine coconut processing under typhoon risk

The Philippines is among the world's largest coconut producers, with processing
concentrated in typhoon-corridor regions [verify: PCA regional statistics]. An
integrated coconut processing complex (ICPC) is the most disruption-vulnerable
configuration in this sector: multi-product (routing carries economic
trade-offs), multi-path (nuts, kernels, shells, husks, and water follow
divergent branches sharing utilities), and feedstock-synchronized (every branch
starves at once when nut supply is cut). Supply disruption is not a stress test
for this plant class — it is the dominant operating risk, with the historical
record (typhoon-driven tree loss producing multi-year feedstock deficits
[verify: FAO/PCA assessments]) anchoring the threat model. The ICPC is thus an
ideal and consequential testbed: topologically rich enough to make
reconfiguration non-trivial, and economically important enough that resilience
gains translate to livelihood outcomes for a large agricultural workforce.

## 1.3 The gap

Three literatures border this problem and none occupies its intersection.
*Process digital twins* supply physics-consistent models but treat topology as
compiled structure. *Network-resilience research* reconfigures abstract flow
networks under disruption but carries no thermodynamics, unit dynamics, or
transient-reachability constraints. *Graph neural networks for process systems*
learn on fixed process graphs — predicting properties *of* a topology, never the
consequences of *changing* it. No published framework makes plant topology a
runtime decision variable of a physics-consistent digital twin under a real-time
budget. That empty intersection is this thesis's target.

## 1.4 The proposed solution

The RDT is a closed sensing–screening–optimizing–verifying loop:

- **Detection** — a hybrid Bayesian online change-point detector with a CUSUM
  drift arm fires on multivariate plant signals when disruption posterior mass
  crosses a threshold.
- **Screening** — a learned surrogate scores each candidate topology change for
  feasibility and multi-attribute impact in milliseconds, pruning a combinatorial
  reconfiguration space before exact optimization.
- **Selection** — a mixed-integer linear program over the screened candidates
  selects and sequences reconfigurations subject to mass balance, capacity,
  pressure/temperature, simultaneity, and safety-exclusion constraints
  auto-derived from the graph.
- **Verification** — a differential-algebraic plant model confirms the selected
  transition is dynamically reachable without constraint violation.

The loop is *recurrent*: it re-decides every cycle as the disruption reveals
itself, and reversible reconfigurations can be unwound when their predicted value
lapses. This recurrence is central — the thesis shows it is what allows imperfect
screening to outperform one-shot perfect foresight.

## 1.5 Research questions and hypotheses

The thesis is organized around five research questions: whether reconfiguration
value is learnable (RQ1), whether learned screening suffices to make real-time
selection tractable and safe (RQ2), whether the full cycle meets its budget
(RQ3), how much resilience runtime reconfiguration buys and how that gain is
structured (RQ4), and what it is worth economically (RQ5). These are formalized
as six falsifiable hypotheses (H1–H6) with pre-registered acceptance criteria and
statistical tests (Chapter 4); their adjudication is the substance of Chapter 6,
and the headline outcomes — H4 resilience and H5 recovery — are met with margin
and robustness, while the learned-generalization hypotheses (H1–H2) resolve into
a reframed scaling question with an honest negative result.

## 1.6 Contributions

This thesis contributes:

1. **The first reactive digital twin** in chemical process engineering — topology
   as a runtime state variable of a physics-consistent twin — demonstrated as a
   working closed-loop system with a 3.1 ms topology-recompilation cost against a
   40 s budget (F#8, F#31).
2. **A validated resilience result**: ΔR = 0.244 [0.237, 0.251] uncapped and
   0.174 [0.168, 0.180] under a pessimistic market, TTR₈₀ reduction 57.7%
   [55.2, 60.2], across 2,000 pre-registered paired runs (F#24, F#26, F#28).
3. **Methodological results for prescriptive-twin evaluation**: the
   comparator-symmetry principle (F#21), the recurrent-versus-oracle diagnostic
   (F#19), and pre-registration catching a *model* artifact rather than analyst
   bias (F#23, F#25).
4. **A documented negative** on graph-attention generalization to unseen topology
   changes, with paired baselines, controls, and a scale floor (F#15, F#18, F#30)
   — offered as a benchmark to beat.
5. **An open-source, reproducible framework**: simulator, disruption library,
   trained-screen recipe, MILP constraint generators, and the full analysis
   pipeline behind a one-command harness (F#29, F#31).

## 1.7 Scope and thesis structure

The thesis validates runtime reconfiguration of an existing physical
superstructure (activating installed lines, bypasses, and mode switches) via
simulation calibrated to Philippine typhoon statistics; design of new physical
connections, cyber-attack threat models, and live plant trials are out of scope
(Chapter 4.5). The document proceeds: Chapter 2 states the mathematical framework;
Chapter 3 reviews the three bordering literatures and consolidates the gap;
Chapter 4 fixes objectives, questions, and hypotheses; Chapter 5 details the
five-phase methodology; Chapter 6 reports results against every hypothesis;
Chapter 7 discusses mechanism, methodological contributions, the negative result,
and limitations; and the publication and dissemination plan (Chapter 10 of the
research lifecycle) frames the two-paper split and the open-source release.

---
*All validation data derive from a physics forward-model simulator; every dataset
row carries `data_class = SYNTHETIC/physics-forward-model`. No real plant data
enters any quantitative claim in this thesis.*
