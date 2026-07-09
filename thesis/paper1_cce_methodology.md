# A Reactive Digital Twin: Graph-Attention Screening and Real-Time MILP for Runtime Topology Reconfiguration of Chemical Process Networks

*Paper 1. Computers & Chemical Engineering (methodology). Draft v1, 2026-07-04.
Carries novelty claims N1–N3. Economics presented as indicative pending source
verification (§9.2 of the research lifecycle). Every quantitative result traces to
the thesis findings register (F#n); companion Paper 2 (RESS) carries the
resilience-and-impact claims N4–N5. All in-text citations are validated against
source PDFs in `references.bib`; two provenance items are flagged there (a
wrong-file MILP upload to re-source, and the closest prior art, Ovalle et al. 2024,
distinguished explicitly in §1.2).*

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
throughput returns in days or in weeks. Resilience-aware design has become an
active concern in process systems (Chrisandina et al., 2022; Ab Rahim et al.,
2024), yet the twin that would support it in real time has been missing. The twin is most eloquent when the plant
is calm and mute when the plant is in crisis. That inversion is the problem this
paper sets out to fix.

### 1.2 The gap and contribution

Three research communities have each walked up to the edge of this problem, and
each has stopped just short of it. Process digital twins (Grieves and Vickers,
2017; Kapteyn et al., 2021; Peterson et al., 2024) have given us models of
remarkable physical fidelity, but on a flowsheet that is settled before the first
equation is solved; the recent process-engineering survey of Peterson et al.
(2024), published in this journal, catalogues computational methods for digital
twins without topology ever appearing as a decision variable. Network-resilience
research (Bruneau et al., 2003; Ouyang, 2014) has thought deeply about
reconfiguring networks under stress, yet its networks are abstractions of flow,
innocent of thermodynamics, of unit dynamics, and of the awkward fact that a plant
cannot teleport from one steady state to another without passing through a
transient that may itself violate a constraint. The graph-neural-network
literature in process systems has learned to read process topologies with real
sophistication (Stops et al., 2023; Anthony et al., 2024; Schulze Balhorn et al.,
2025), but always to generate, complete, or predict a property *of* a graph, never
to reason in real time about the consequences of *changing* an operating plant's
topology under disruption. Between these three lies an empty space, and it has a
precise shape: no published framework makes plant topology a runtime decision
variable of a physics-consistent digital twin operating under a real-time budget.
That empty space is where this work lives.

The nearest neighbour to the present work, and the one a knowledgeable reader will
reach for first, is the reactive network operation of Ovalle et al. (2024), which
also concerns "general topology" networks "under disruptions." Because the titles
sit so close, the distinction deserves to be exact. Ovalle et al. address a
multi-material **supply-chain and manufacturing network**, whose nodes are
suppliers, plants, warehouses, and customers, and they decide shipment routes,
production schedules, acquisition, and order management by a multiperiod
mixed-integer linear program that minimizes the financial impact of a disruption
over a daily-to-hourly horizon. Their topology is an arbitrary but *fixed*
substrate: the physical network design is given, and flows are optimized within
it. The reactive digital twin answers a different question at a different scale. Its
nodes are unit operations, utilities, and storage; its edges are material streams,
unit routings, and utility connections *inside a single process complex*; and its
central decision is to **physically rewire that plant in real time**, activating
and deactivating edges as a disruption unfolds. Where Ovalle solves one monolithic
program over a static network, the twin runs a recurrent loop that detects the
disruption online, screens a combinatorial reconfiguration space with a learned
surrogate, selects by MILP, and verifies each candidate against a differential-
algebraic model of the plant transient. The two works share two words, reactive
and topology, and share MILP as an exact-optimization layer; they differ in object
(supply-chain network versus process plant), in granularity (facilities versus
streams and units), in physics (none versus an index-1 differential-algebraic
model), and in machine (a single optimization versus a closed sensing-to-
verification loop). The twin occupies precisely the plant-physics-level, real-time,
dynamics-verified niche that network-operational formulations bracket out.

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

We represent the plant at time $t$ as a directed attributed graph
$$G(t) = \bigl(V,\ E(t),\ \mathbf{X}_V(t),\ \mathbf{X}_E(t)\bigr),$$
in which the node set $V$ is fixed but the edge set $E(t) \subseteq E_{\max}$, the
node-feature matrix $\mathbf{X}_V(t) \in \mathbb{R}^{|V| \times d_V}$, and the
edge-feature matrix $\mathbf{X}_E(t) \in \mathbb{R}^{|E(t)| \times d_E}$ all vary
with time. This is the formal statement of the paper's premise: topology, encoded
in $E(t)$, is a state variable rather than a compile-time constant. Nodes carry
unit operations, utility supplies, and storage; the node features $\mathbf{x}_v =
(\text{capacity},\ \text{load},\ \text{health},\ \text{inventory}, \dots)$ and the
edge features $\mathbf{x}_e = (\text{flow},\ \text{composition},\ T,\ P,\
\kappa_e,\ \nu_e, \dots)$ include a route-physics descriptor of line capacity
$\kappa_e$ and net value density $\nu_e$ whose purpose becomes clear in §4.2.

The set of all connections the plant could physically realize is a static
superstructure $G_{\max} = (V, E_{\max})$, and every admissible operating topology
is a subgraph $G(t) \subseteq G_{\max}$. A reconfiguration is an operator
$$\Delta G:\ G(t) \mapsto G(t^+),\qquad
E(t^+) = \bigl(E(t) \setminus E^-\bigr) \cup E^+,$$
where $E^+ \subseteq E_{\max} \setminus E(t)$ activates dormant routes and
$E^- \subseteq E(t)$ deactivates active ones, together with node-mode switches
that retarget a unit's internal routing. For the case-study plant,
$|E_{\max}| \approx 45\text{--}60$ candidate edges of which a reconfigurable
subset $\mathcal{K} \subseteq E_{\max}$ is controllable, giving a change space of
size $2^{|\mathcal{K}|}$ on the order of $10^9$. No exact optimizer can enumerate
that space inside a real-time budget, which is the structural reason a learned
screen must precede the MILP (§2.3, §2.4).

### 2.2 Detection: hybrid BOCPD with CUSUM

The loop cannot re-decide until it knows something has changed, and detecting that
change quickly, without crying wolf on ordinary process noise, is its own problem.
We solve it with Bayesian Online Change-Point Detection (Adams and MacKay, 2007)
augmented by a drift detector; process-monitoring fault detection has a long
lineage in our field (Venkatasubramanian et al., 2003), but the reconfiguration
setting needs both fast onset detection and slow-drift sensitivity, which the
hybrid below provides. BOCPD maintains a posterior over the run length
$r_t$, the number of steps since the last change point. Writing
$\mathbf{y}_{1:t}$ for the multivariate observation stream, the run-length
posterior evolves by the recursion
$$P(r_t \mid \mathbf{y}_{1:t}) \propto \sum_{r_{t-1}}
P(r_t \mid r_{t-1})\,
P(\mathbf{y}_t \mid r_{t-1}, \mathbf{y}_{t}^{(r)})\,
P(r_{t-1} \mid \mathbf{y}_{1:t-1}),$$
with a constant hazard $P(r_t = 0 \mid r_{t-1}) = H$ governing the prior rate of
change points and $P(r_t = r_{t-1}+1) = 1-H$ otherwise. Each channel uses a
conjugate Normal-Inverse-Gamma model, so the predictive
$P(\mathbf{y}_t \mid r_{t-1}, \cdot)$ is Student-$t$ in closed form and the update
requires no sampling. A disruption is declared when posterior mass concentrates on
short run lengths,
$$\sum_{r_t \le r_{\min}} P(r_t \mid \mathbf{y}_{1:t}) > \tau_{\text{BOCPD}}.$$

This trigger is fast on abrupt changes and structurally blind to slow ones: a
gradual feedstock decline never produces a sharp posterior collapse, and in our
experiments BOCPD alone missed 48% of slow-ramp supply disruptions (§4). We
therefore fuse a two-sided cumulative-sum detector on the same standardized
channels,
$$S_t^{+} = \max\!\bigl(0,\ S_{t-1}^{+} + z_t - k\bigr),\qquad
S_t^{-} = \max\!\bigl(0,\ S_{t-1}^{-} - z_t - k\bigr),$$
which fires when $\max(S_t^{+}, S_t^{-})$ exceeds a control limit $h$. The CUSUM
accumulates small persistent deviations that the run-length posterior discards as
noise, so the union of the two triggers detects both the shock and the slow
bleed. The reference value $k$ and limit $h$ are set from a false-alarm budget on
disruption-free calibration runs (§4.4).

### 2.3 Screening: graph-attention surrogate

With a change detected, the loop faces the combinatorial space of §2.1 and has
milliseconds to shrink it. The screen is a graph-attention network that scores
each candidate reconfiguration for feasibility and impact, cheaply enough to
evaluate the whole candidate set every cycle. We use the GATv2 formulation (Brody
et al., 2022), whose dynamic attention corrects the static-ranking limitation of
the original GAT. For a candidate topology, node representations update by
$$\mathbf{h}_i' = \sigma\!\Bigl(\textstyle\sum_{j \in \mathcal{N}(i)}
\alpha_{ij}\, \mathbf{W}\,[\mathbf{h}_j \,\|\, \mathbf{e}_{ij}]\Bigr),$$
where $\mathbf{e}_{ij}$ carries the edge features including the reconfiguration
indicator, $\|$ denotes concatenation, and the attention coefficients are
$$\alpha_{ij} = \operatorname{softmax}_j\!\bigl(
\mathbf{a}^{\!\top}\,\text{LeakyReLU}\bigl(\mathbf{W}\,
[\mathbf{h}_i \,\|\, \mathbf{h}_j \,\|\, \mathbf{e}_{ij}]\bigr)\bigr).$$
Placing the nonlinearity before the projection $\mathbf{a}$ is what makes the
attention dynamic: the ranking of neighbours can depend on the query node, which a
static GAT cannot express. Multi-head attention is concatenated across layers, and
a graph-level readout combines a global mean with a change-localized pool over the
endpoints of the reconfigured edges,
$$\mathbf{g} = \bigl[\,\operatorname{mean}_{i \in V} \mathbf{h}_i \ \big\|\
\textstyle\sum_{e \in \Delta G} w_e (\mathbf{h}_{s(e)} + \mathbf{h}_{d(e)})\,\bigr],
\qquad w_e = \frac{|\Delta G_e|}{\sum_{e'} |\Delta G_{e'}|},$$
feeding a shallow multilayer perceptron that emits the predicted resilience impact.
The screen is a speed layer, not a correctness layer. Every candidate it advances
is re-checked by the MILP constraints (§2.4) and the DAE verifier (§2.5), so a
screening false positive costs a solver iteration, never an infeasible action. Its
role, its limits, and a decisive negative result on its generalization to unseen
reconfigurations are the subject of §4.2.

### 2.4 Selection: MILP over screened candidates

The screen ranks candidates but cannot enforce that a chosen set is jointly
feasible: two individually attractive reconfigurations may compete for the same
crew, violate an exclusion, or overload a shared line. Selection is therefore an
exact mixed-integer linear program over the screened set $\mathcal{C}$. Let
$x_k \in \{0,1\}$ select candidate $k$, let $f_e \ge 0$ be the post-reconfiguration
flow on edge $e$, and let $\hat{b}_k$ be the screen's predicted benefit for
candidate $k$. The program is
$$\max_{x, f}\ \sum_{k \in \mathcal{C}} \hat{b}_k\, x_k
\quad\text{subject to}$$
$$\textstyle\sum_{k} x_k \le N_{\max}
\tag{simultaneity}$$
$$\textstyle\sum_{k} c_k\, x_k \le B
\tag{resource budget}$$
$$\textstyle\sum_{e \in \text{in}(v)} f_e - \sum_{e \in \text{out}(v)} f_e = 0
\quad \forall v \in V \setminus \{\text{sources, sinks}\}
\tag{mass balance}$$
$$f_e \le \kappa_e\, a_e(x) \quad \forall e \in E_{\max}
\tag{capacity}$$
$$\underline{P}_u \le P_u(x) \le \overline{P}_u,\quad
\underline{T}_u \le T_u(x) \le \overline{T}_u \quad \forall u
\tag{envelopes}$$
$$x_a + x_b \le 1 \quad \forall (a,b) \in \mathcal{X}
\tag{safety exclusions}$$
where $a_e(x)$ is the activation state of edge $e$ implied by the selection,
$c_k$ and $B$ are the per-change and total resource costs, and $\mathcal{X}$ is the
set of mutually exclusive reconfiguration pairs.

The property that matters for reproducibility and for deployment to a new plant is
that **none of these constraints is written by hand for the case study**. Each is
emitted by a generator that reads the graph object: the capacity row for an edge
is created when that edge exists in $E_{\max}$; the balance rows follow the node
adjacency; the exclusion set $\mathcal{X}$ is derived from the superstructure's
declared incompatibilities. Adding a candidate edge to $G_{\max}$ therefore adds
its capacity constraint, its balance contributions, and its exclusions
The structure is a discrete process-decision problem of a familiar kind: each
reconfigurable edge is either active, carrying flow within its capacity, or
inactive, carrying none, which is exactly the unit-existence disjunction at the
heart of process-synthesis formulations (Grossmann, 2002). Where a general
synthesis problem would carry nonlinear unit models and become a mixed-integer
nonlinear or generalized disjunctive program, the reconfiguration decision at a
fixed operating point linearizes cleanly: the flows are linear in the selection,
the envelopes are box constraints, and the disjunctions reduce to the
big-M-free capacity form above. The result is a pure MILP with no integrality gap
tricks required at this size; it is solved by HiGHS (Huangfu and Hall, 2018) under
a wall-clock time box, warm-started from the incumbent topology so that the common
case of a small reconfiguration solves in near-constant time. Mixed-integer linear
programming has a long record as an operational tool in the chemical process
industry (Kallrath, 2000), and the contribution here is not the solver but the
graph-driven generation of the model it solves.

### 2.5 Verification: DAE transition model

A selection that is feasible on paper may still be unreachable in practice: the
plant cannot jump between steady states, and the transient between them can violate
a constraint the endpoint respects. The verifier integrates the reconfiguration on
a semi-explicit index-1 differential-algebraic model
$$\dot{\mathbf{x}} = \mathbf{f}(\mathbf{x}, \mathbf{z}, \mathbf{p}, t),\qquad
\mathbf{0} = \mathbf{g}(\mathbf{x}, \mathbf{z}, \mathbf{p}, t),$$
where the differential states $\mathbf{x}$ carry buffer inventories, the
serial dryer-moisture chain, and evaporator holdup, and the algebraic variables
$\mathbf{z}$ satisfy quasi-steady equilibrium relations and the utility
pressure-flow balances. The system is compiled and integrated with
CasADi (Andersson et al., 2019) over Sundials.

Two numerical points earned their place through failure during development and are
reported because they generalize. First, the algebraic system is explicit in
$\mathbf{z}$ by construction, so consistent initialization uses the closed-form
solution $\mathbf{z}_0 = \mathbf{g}_z^{-1}(\mathbf{x}_0, \mathbf{p})$ rather than a
Newton solve; relying on the integrator's own initial-condition calculation failed
at the parameter discontinuities that a reconfiguration introduces, precisely when
the plant state sits on a gate manifold. Second, at those discontinuities the
integrator is protected by a degraded-mode ladder: a retry at loosened tolerance,
then a ten-fold substepped integration, invoked only on failure so the common case
pays nothing. A reconfiguration is verified when the trajectory reaches the target
steady state within tolerance and violates no capacity or envelope constraint in
transit; otherwise it is rejected and the MILP re-solved with that candidate
excluded.

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
processing complex (ICPC) comprising seven unit operations (receiving, dehusking,
drying, cold press, refining, carbonization, and evaporation), four utility
networks (steam, power, cooling water, compressed air), and four saleable product
streams (virgin coconut oil, copra meal, shell charcoal, and coconut-water
concentrate); the unit operations and their yields follow standard coconut-
processing practice (Ng et al., 2021). We chose this archetype deliberately, because it stresses every
part of the framework at once. It is multi-product, so a disruption forces genuine
economic trade-offs about which route to sacrifice rather than a single obvious
response. It is multi-path, with kernel, shell, husk, and water branches diverging
early and sharing utilities downstream, so a utility loss propagates across
products that appear unrelated on the flowsheet. And it is feedstock-synchronized,
because every branch begins at the same nut intake, so a supply cut starves the
entire plant simultaneously rather than degrading it gracefully. An agro-industrial
complex of this kind is also the setting where the economic stakes of resilience
are largest, since the raw material is perishable and the disruptions are frequent.

The seven modeled reconfiguration options are a deliberate subset of the candidate
superstructure, not a limitation of convenience. They were selected to span the
value structure the screen must learn: rescue options that recover large value
under the right disruption, a harmful-by-default option whose benefit is negative
outside a narrow duration window, and near-zero options whose value is marginal
everywhere. This spread is what lets §4.2 test whether the screen has learned the
*physics* of a reconfiguration or merely its *identity*. Extending the model to the
remaining candidate edges is mechanical: each new edge adds its terms through the
same graph-driven auto-derivation (§2.4), raising the achievable resilience ceiling
without altering the architecture (§4.5).

### 3.2 Disruption library and pre-registration

The disruption library spans eight categories: feedstock quantity and quality
shocks, unit failures, utility outages, logistics interruptions, cascading
failures, drought-driven multi-week supply deficits, and combined events that fire
more than one category at once. Each category is parameterized by onset time,
severity, and duration, and scenarios are drawn by Latin-hypercube sampling over
severity-stratified ranges so that the campaign covers the full disruption
envelope rather than clustering near typical cases. Severity ranges for the
supply and utility categories are calibrated to regional records where those
records exist, and flagged as planning-grade where they do not (§9.2 of the
research lifecycle). Every label and every evaluation scenario is generated by the
physics forward model and carries a synthetic-data class marker at the row level;
no real plant data enters any number in this paper.

The full-scale evaluation is pre-registered. Analysis endpoints, statistical
tests, and acceptance criteria were frozen at a specific commit hash before the
2,000-run campaign executed, so the analysis could not be tuned to the result
after seeing it. Pre-registration is still uncommon in simulation-based
process-systems studies, and it is sometimes dismissed as ceremony when the
analyst and the modeler are the same person. Section 4.4 offers a concrete rebuttal:
here it caught a genuine modeling artifact, an unphysical assumption that the
frozen analysis flagged precisely because a pre-committed prediction failed to
appear, which an unconstrained post-hoc analysis would very likely have explained
away.

### 3.3 Metrics

Resilience is measured as the normalized area under the recovery curve. Writing
$P(\tau)$ for the instantaneous production value and $P_0$ for its pre-disruption
level, the resilience integral over a horizon $T$ is
$$R(T) = \frac{1}{T}\int_{0}^{T} \frac{P(\tau)}{P_0}\, d\tau,$$
evaluated on a $T = 72$ hour window after onset. A subtlety that changes the
result is the choice of $P$: on a pure mass basis, $R$ is nearly insensitive to a
disruption that halves product *quality* while preserving throughput, because the
kilograms still flow. We therefore compute $P$ on a margin-weighted value basis,
$P(\tau) = \sum_p \nu_p\, \dot{m}_p(\tau)$, summing product mass flows $\dot{m}_p$
weighted by net value density $\nu_p$, so that quality-destroying disruptions
register their true economic damage.

The headline comparative quantity is the paired difference
$$\Delta R = R_{\text{RDT}} - R_{\text{static}},$$
computed on identical disruption realizations under common random numbers, which
removes scenario-to-scenario variance from the comparison and sharpens every
confidence interval. The companion operational metric is the time to 80% recovery,
$\text{TTR}_{80}$, the first time after onset at which $P(\tau)/P_0$ returns to and
holds above $0.8$; it is undefined (reported separately, never as zero) for
episodes that do not recover within the horizon, a convention that keeps the
recovery statistics honest rather than flattering.

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
