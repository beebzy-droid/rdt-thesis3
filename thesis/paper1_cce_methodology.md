# A Reactive Digital Twin: Graph-Attention Screening and Real-Time MILP for Runtime Topology Reconfiguration of Chemical Process Networks

*Paper 1. Computers & Chemical Engineering (methodology). Draft v1, 2026-07-04.
Carries novelty claims N1–N3. Economics presented as indicative pending source
verification (§9.2 of the research lifecycle). Every quantitative result traces to
the thesis findings register (F#n); companion Paper 2 (RESS) carries the
resilience-and-impact claims N4–N5.*

**Target length:** ~8,500 words + 6 figures. **Article type:** full research paper.

---

## Abstract

Digital twins in chemical process engineering treat plant topology, the network
of streams, unit routings, and utility connections, as fixed at build time. This
fails under supply-chain disruption, when the plant survives by reconfiguring its
network and a topology-frozen twin can neither represent nor prescribe the
response. We present the first digital twin that reconfigures its own process-
network topology in real time. The architecture couples four engines in a
recurrent loop: Bayesian online change-point detection; a graph-attention
surrogate screening candidate topology changes for feasibility and impact; a
mixed-integer linear program selecting reconfigurations under constraints
auto-derived from the process graph; and a differential-algebraic model verifying
dynamic reachability. Topology is a runtime data structure, with the model graph
recompiling in 3.1 ms against a 40 s budget. On a physics-based coconut-processing
model across 2,000 pre-registered paired runs, runtime reconfiguration improves a
72-hour resilience integral by ΔR = 0.244 (95% CI [0.237, 0.251]). This margin
widens to 0.294 [0.286, 0.302] against an optimistic bound on any continuous
controller, confirming that the advantage is topological rather than a
continuous-control artifact. We report, against interest, that graph-attention
screening does not generalize to unseen reconfigurations at the data scale
examined, a negative that the layered architecture renders non-blocking, and that
reconfiguration value is disruption-conditional, so a recurrent loop applying
imperfect screening repeatedly outperforms one-shot perfect foresight. The
framework is released open-source with a one-command reproducibility harness.

**Keywords:** digital twin; process network reconfiguration; graph neural
networks; mixed-integer linear programming; real-time optimization; resilience.

## 1. Introduction

### 1.1 Motivation

A digital twin is a promise: that a virtual replica, kept faithful to its physical
counterpart, can watch the plant, foresee its trouble, and eventually tell it what
to do. The field has made good on the first two parts of that promise and is
reaching for the third. Monitoring twins gave way to predictive twins, and
predictive twins to prescriptive ones that close the loop, wiring a plant model to
an optimizer that trims setpoints, rebalances splits, and reallocates utilities in
pursuit of some objective. It is a genuine arc of progress. But it has been built
on a quiet assumption that no one has had reason to question, because in ordinary
operation it never bites: that the *shape* of the plant, which stream feeds which
vessel, which bypass sits idle, which product route is open, is a fixed thing,
compiled into the model when it is built and untouched thereafter. The optimizer
may turn every knob it likes, so long as the pipes stay where they are.

That assumption holds right up until the moment it matters most. When a typhoon
severs the feedstock supply, when a steam header trips, when a unit is walled off
for an unplanned repair, the *physical* plant does not sit still and optimize its
setpoints. It reconfigures. Operators reroute half-processed material down paths
the design never emphasized, switch a boiler from its usual fuel to whatever is at
hand, bypass the lost capacity, and quietly rewrite the product slate to salvage
value from what remains. This is how real plants survive real disruptions, and it
is precisely the behavior a topology-frozen twin cannot follow. It cannot draw the
reconfigured plant, cannot trace a recovery trajectory through a network it is
forbidden to redraw, and so it falls silent in exactly the window, the first hours
after onset, when the routing choices being made on the plant floor decide whether
throughput returns in days or in weeks. The twin is most eloquent when the plant
is calm and mute when the plant is in crisis. That inversion is the problem this
paper sets out to fix.

### 1.2 The gap and contribution

Three research communities have each walked up to the edge of this problem, and
each has stopped just short of it. Process digital twins (Grieves, 2014; Rasheed
et al., 2020; Kapteyn et al., 2021) have given us models of remarkable physical
fidelity, but on a flowsheet that is settled before the first equation is solved.
Network-resilience research (Bruneau et al., 2003; Ouyang, 2014) has thought
deeply about reconfiguring networks under stress, yet its networks are abstractions
of flow, innocent of thermodynamics, of unit dynamics, and of the awkward fact
that a plant cannot teleport from one steady state to another without passing
through a transient that may itself violate a constraint. The graph-neural-network
literature has learned to read process topologies with real sophistication, but
always to predict a property *of* a fixed graph, never to reason about the
consequences of *changing* it. Between these three lies an empty space, and it has
a precise shape: no published framework makes plant topology a runtime decision
variable of a physics-consistent digital twin operating under a real-time budget.
That empty space is where this work lives.

This paper contributes: (N1) the first reactive digital twin architecture with
runtime topology reconfiguration in chemical process engineering; (N2) the first
application of graph-attention screening to predict feasibility and impact of
process-network topology changes, reported here with an honest negative on its
generalization limit; and (N3) a MILP reconfiguration optimizer whose full
constraint set is auto-derived from process-graph structure and solves in real
time. The resilience quantification and economic-impact claims (N4–N5) are
developed in a companion paper.

## 2. Framework

The RDT is a closed sensing–screening–optimizing–verifying loop. We state each
engine at the fidelity needed to reproduce it; the plant graph is defined first
(§2.1), then the four engines (§2.2–2.5), then their real-time composition (§2.6).

### 2.1 Process network as a runtime graph

The plant at time *t* is a directed attributed graph G(t) = (V, E(t), X_V(t),
X_E(t)) whose edge set, node features, and adjacency are *time-varying*: topology
is a state variable, not a constant. Nodes are unit operations, utility supplies,
and storage; node features encode capacity, load, health, and buffer inventories;
edge features encode flow, composition, temperature, pressure, and a route-physics
descriptor (capacity and net value density). A topology change ΔG is a finite set
of edge activations and node-mode switches drawn from a static superstructure
G_max of all physically installable connections; every admissible G(t) is a
subgraph of G_max. For the case-study plant, |E(G_max)| ≈ 45–60 candidate edges
give a combinatorial change space on the order of 2³⁰, which is why a learned
screen precedes exact optimization.

### 2.2 Detection: hybrid BOCPD + CUSUM

Disruption onset is detected by Bayesian Online Change-Point Detection (Adams &
MacKay, 2007), a recursive run-length posterior with a Normal-Inverse-Gamma
predictive per channel, fused with a two-sided CUSUM drift detector. The fusion
is not incidental: run-length triggers are structurally blind to slow supply
ramps (48% missed on gradual feedstock decline for BOCPD alone), which the CUSUM
arm catches. The trigger fires when posterior mass on short run lengths exceeds a
threshold; the CUSUM arm fires when any channel's cumulative deviation exceeds a
control limit.

### 2.3 Screening: graph-attention surrogate

A GATv2 surrogate (Brody et al., 2022) with edge features scores each candidate
ΔG for feasibility and a multi-attribute impact vector. The screen prunes the
combinatorial change space to a tractable candidate set for exact optimization; it
is a speed layer, not a correctness layer; every candidate it passes is re-checked
by the downstream MILP constraints and DAE verifier. Its role, limits, and a
decisive negative result on its generalization are reported in §4.2.

### 2.4 Selection: MILP over screened candidates

Given the screened candidate set, a mixed-integer linear program selects and
sequences reconfigurations. Binary variables select candidates; continuous
variables carry post-reconfiguration flows. The objective maximizes weighted
predicted benefit subject to six constraint classes: a simultaneity limit,
resource budget, node mass balance, pipe capacity, pressure/temperature envelopes,
and pairwise safety exclusions. The defining property is that **every constraint
is auto-derived from the graph object**: activating an edge in G_max adds its
capacity constraint, its balance terms, and its exclusion entries with no hand
coding (N3). The formulation is a pure MILP solved by HiGHS with a wall-clock
time box and warm start from the incumbent topology.

### 2.5 Verification: DAE transition model

The selected transition is verified on a semi-explicit index-1 differential-
algebraic model (CasADi/Sundials CVODE), with differential states for inventories,
dryer-moisture chains, and evaporator holdup; algebraic equations for
quasi-steady equilibrium and utility pressure-flow balances. Consistent
initialization uses the closed-form algebraic solution, with a degraded-mode
integration ladder (loose tolerance, then substepping) at parameter
discontinuities. A transition is verified if the trajectory reaches the target
steady state without constraint violation.

### 2.6 Real-time composition and the runtime-topology architecture

The four engines compose asynchronously: detection runs continuously; screening,
selection, and verification run on trigger, each with a hard time budget and a
defined degraded mode, so the cycle never blocks. The architectural enabler is
that **the plant model's topology is a runtime data structure** rather than
compiled code (N1): a graph-to-DAE compiler regenerates the model when topology
changes, in 3.1 ms against a 40 s budget (F#8, F#31), with the regenerated model
matching a hand-coded reference to machine precision. This is the barrier the
digital-twin literature treats as definitional, that changing topology means
regenerating and re-initializing an offline model, reduced to an implementation
choice.

## 3. Case study and experimental design

### 3.1 Reference plant

The demonstration plant is a physics-based model of an integrated coconut
processing complex (seven unit operations: receiving, dehusking, drying, cold
press, refining, carbonization, and evaporation; four utility networks; four product
streams). It is chosen as a topologically rich, disruption-vulnerable
agro-industrial archetype: multi-product with economic routing trade-offs,
multi-path with shared utilities, and feedstock-synchronized. The seven modeled
reconfiguration options are a deliberate subset of the candidate superstructure,
selected to span the value structure the screen must learn, spanning rescue options, a
harmful-by-default option, and near-zero options, with extension to the full
candidate set mechanical through the same auto-derivation path (§4.5).

### 3.2 Disruption library and pre-registration

Eight disruption categories (feedstock quantity/quality, unit failure, utility
outage, logistics, cascade, drought, combined) are sampled by Latin-hypercube over
severity-stratified parameter ranges. All labels and evaluation scenarios derive
from the physics forward model and carry a synthetic-data class marker; no real
plant data enters any result. The full-scale evaluation is **pre-registered**:
analysis endpoints, statistical tests, and acceptance criteria frozen at a commit
hash before the campaign executed (F#23), a discipline uncommon in process-systems
ML and, as §4.4 shows, one that caught a model artifact rather than merely analyst
bias.

### 3.3 Metrics

Resilience is the normalized area under the recovery curve, R(T) = (1/T)∫₀ᵀ
P(τ)/P₀ dτ, on a margin-weighted value basis (mass-basis R is insensitive to
quality-destroying disruptions). The headline comparative quantity is ΔR = R(RDT)
− R(static), computed pairwise on identical disruption paths with common random
numbers. The companion operational metric is time-to-80%-recovery.

## 4. Results

### 4.1 Simulator verification and MILP performance

The graph-to-DAE compiler matches a hand-coded reference to 1.4×10⁻¹⁴ over 30-day
trajectories and compiles in 3.1 ms; mass-balance closure is below 0.5%. The MILP
selector solves in 4.7 ms median at the wired portfolio size, three orders of
magnitude inside the 60 s cycle budget, so real-time selection is never the
binding constraint (N3 latency claim). Verification of the auto-derivation:
constraint generators emit HiGHS constraints directly from the graph object, unit-
tested against hand-built miniature instances.

### 4.2 Screening: parity in-distribution, a negative result on generalization

In-distribution, the graph-attention screen reaches R² = 0.644 ± 0.177 on
scenario-disjoint folds, at parity with a flat gradient-boosted baseline on the same
features (0.623 ± 0.159), seed-stable. Relational structure adds nothing a flat
model cannot extract at this data scale (F#14).

The consequential result is on *generalization to unseen topology changes*, the
capability that would justify a graph model over a tabular one. Across a
generalization-onset sweep (training on option subsets of size k ∈ {3,4,5,6},
testing transfer to held-out options, both models paired on identical splits),
**no model generalizes, and the graph model degrades monotonically with option
diversity**: median transfer R² negative at every k, never exceeding the flat
baseline, with no rank signal (Spearman ρ ≈ 0) (F#15, F#18, F#30). The mechanism,
established by an option-identity-blind control, is that the change descriptor
encodes option *identity* rather than option *physics*; descriptive edge features
help a tree model split on them but are diluted through message passing at ~10³-
record scale. We report this as a **scale floor**, not an impossibility: the
untested regime is 10⁴–10⁵ examples with richer edge semantics, and the published
curve is a baseline for successor work. Crucially, the layered architecture makes
the negative non-blocking, because the screening slot is filled by the physics-featurized
tabular model, which dominates every measured axis, and system performance (§4.3)
does not gate on the graph model (N2, reported with its honest limit).

### 4.3 Resilience improvement and comparator hardening

The headline comparison was hardened across five comparator iterations, and the
sequence is itself a result. Against a passive static twin the recurrent loop
scores ΔR = 0.190 [0.169, 0.211], *above* the one-shot perfect-foresight oracle
(0.187): recurrence with reversibility beats one-shot optimality, because the loop
composes reconfigurations sequentially and unwinds errors as the disruption
reveals itself (F#19). This inversion, imperfect information applied repeatedly
outperforming perfect information applied once, is, to our knowledge, unreported
in the digital-twin evaluation literature and is the paper's central conceptual
finding.

Strengthening the comparator exposed a methodological trap. An onset-scheduled
strong static policy produced a *formal false negative* (ΔR = 0.117 [0.093,
0.142]), but against an RDT arm running an inferior continuous policy with
pre-burned buffers. Restoring arm symmetry (both arms on the winning continuous
schedule; the static comparator retaining an oracle-onset advantage) gave ΔR =
0.241 [0.215, 0.267] (F#21). The lesson generalizes: **comparator strength without
arm symmetry produces false negatives** in prescriptive-twin evaluation; the
0.117 would have wrongly rejected the effect.

At full scale, across 2,000 pre-registered paired runs with hybrid detection gating both the
continuous-regime switch and topology decisions, ΔR = 0.2438, 95% CI [0.2368,
0.2511], Wilcoxon p ≈ 10⁻³¹⁰. A final objection, that a continuous controller
(MPC on fixed topology) might reclaim the gap, is bounded without building the
controller: the clairvoyant two-regime envelope max(V_slow, V_fast) upper-bounds
any causal continuous controller over the draw-regime action set, and is a genuine
strengthening (R = 0.666 vs the realized static 0.637). The RDT clears it with
**ΔR = 0.294 [0.286, 0.302]** (F#34), a margin *exceeding* the headline, because
a stronger continuous baseline widens rather than narrows the gap: topology
adaptation accesses rerouting and product-slate value that no draw-rate policy can
reach. The residual, a continuous draw-rate-modulation controller, is not
bounded here and is named future work.

### 4.4 Pre-registration as artifact detection

The frozen analysis plan predicted an inverted-U dose–response (resilience gain
peaking at intermediate severity). Its *absence* in the frozen output was the
anomaly that exposed an unrealistic modeling assumption: an uncapped purchased-
input market that, at extreme regional disruption, sourced replacement feedstock
from a market the same disruption had struck (F#25). Introducing a market-
availability parameter φ recovered a physically sensible plateau and established a
reporting rule whereby the supply-sensitive categories' gains are reported as a function
of φ, not a scalar. Pre-registration here caught a *model* artifact, not analyst
bias; we offer this as evidence that pre-registration earns its place in
simulation-based process-systems studies.

### 4.5 Scope of the demonstration

The result is demonstrated on one plant archetype with seven of a larger candidate-
edge set. The seven span the rescue/harmful/near-zero value classes (verified by
the option–disruption value matrix); extending to the full set is mechanical, each
edge adding its terms through the same auto-derivation. The *method*, layered
screening over a physics-consistent process graph, is plant-agnostic; the case
study is the demonstration, and the open-source release lets others substitute
their own plant.

## 5. Discussion

**Why topology adaptation delivers.** It would be tempting to attribute the
result to some single clever component: a well-tuned detector, a sharp screen, an
elegant MILP. The data refuse that reading. What the experiments keep showing,
from three unrelated directions, is something simpler and more stubborn: the right
move under disruption depends entirely on *which* disruption, and on how far it has
revealed itself. An option that rescues a long outage actively harms a short one,
the two separated by a crossover near sixty hours. A screen that knows the outage
duration captures a full quarter more of the value variance than one that does
not. Even the humble, non-topological question of how fast to draw down inventory
flips its sign between a supply shock and a unit failure. None of these is a tuning
detail; each is the same lesson wearing different clothes. *The value of a
resilience decision is conditional on the disruption.* A static twin is blind to
all of it, not because it is poorly built but because it is structurally forbidden
from re-deciding once the world has moved. The reactive twin's advantage, then, is
not any one of its parts. It is the compounding, cycle after cycle, of decisions
made conditional on information that only arrives as the crisis unfolds. The
sharpest evidence for this is also the most counterintuitive result in the paper:
a loop running an *imperfect* screen, but running it repeatedly and reversibly,
beat a one-shot oracle handed *perfect* foresight (§4.3). Perfect knowledge used
once is worth less than fallible knowledge used again and again, because
recurrence turns every prediction error from a permanent scar into a passing one.

**Detection latency is policy-dependent.** Measured detection delay was not a net
cost. Under a hoard-then-deploy continuous policy, undetected hours are bridge-
stock-accumulation hours. The cost of detection latency is a property of the policy
it gates, not of the detector, a coupling absent from the detection literature's
delay-minimization framing.

**The negative result, honestly.** The graph model does not generalize to unseen
reconfigurations at reachable scale. We neither hide this nor let it block the
system: the architecture's layering is precisely what decouples system performance
from learner performance, and the tabular screen carries the headline. The
constructive reading, that feature *semantics*, not architecture, is the
productive direction at small scale, is the actionable takeaway for successor
work.

**Real-time budget.** Compute time is met with orders-of-magnitude margin, but
this is a compute-latency result: the deployed end-to-end cycle at production
sampling rates was not tested (the simulation grid floors it) and is future work.
We report H-level cycle compliance as *not tested at production conditions* rather
than met, to keep the claim precise.

## 6. Conclusions

We presented the first digital twin that reconfigures its own process-network
topology in real time, enabled by treating the model graph as a runtime data
structure (3.1 ms recompilation) and by a layered screen–select–verify pipeline
whose MILP constraints are auto-derived from graph structure. On a physics-based
coconut-processing case study under pre-registered evaluation, runtime
reconfiguration improved a 72-hour resilience integral by ΔR = 0.244 [0.237,
0.251], widening to 0.294 against a clairvoyant continuous-control bound; the
advantage is topological, not a continuous-control artifact. We reported, against
interest, that graph-attention screening does not generalize to unseen
reconfigurations at the data scale examined, and that the layered architecture
makes this non-blocking. The framework, disruption library, and analysis pipeline
are released open-source with a one-command reproducibility harness. The
resilience-quantification and economic-impact results appear in the companion
paper.

## Data and code availability

Complete simulator, disruption-scenario generator, trained-screen recipe, MILP
constraint library, and analysis pipeline are released under a permissive license
with a one-command reproducibility harness (`make reproduce`) and a determinism-
verified model-rebuild path. All datasets are synthetic, generated by the physics
forward model, and marked as such at the row level.

## Indicative economics (scoped)

For a reference-scale complex, the resilience gain corresponds to an indicative
avoided-loss on the order of ₱90–100 M/yr at planning-grade prices and disruption
frequencies; these figures are illustrative pending source verification and are
not load-bearing for the methodological claims of this paper. The economic case is
developed, with verified parameters, in the companion paper.

---
*Figures (6): F1 headline ΔR by category with φ-robustness; F7 comparator-
hardening waterfall; F9 N2 generalization-onset (two-panel); a framework schematic
(new, TODO); a recovery-curve exemplar (from F5); the detection ROC/delay (from
F6). Companion Paper 2 carries F2–F4 (φ-curve, dose–response, TTR) and the
economic figures.*
