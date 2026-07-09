# Chapter 7 — DISCUSSION

*Draft v1, 2026-07-04. Claims trace to FINDINGS.md (F#n) and Chapter 6 sections.
Planning-grade parameters remain flagged; nothing in this chapter upgrades an
unverified number into a citable one (§9.2; `check_provenance.py --strict`).*

## 7.1 Answers to the research questions

**RQ1 (learnability of topology-change value).** Reconfiguration value is
learnable in-distribution to R² = 0.868 with oracle features and 0.623 with the
deployable state-only set (F#10, F#13); the 0.245 gap is the measured value of
disruption characterization, dominated by unobservable outage duration. The
graph-relational hypothesis embedded in RQ1 — that message passing extracts
signal a flat model cannot — is answered negatively at this scale: parity
in-distribution (0.644 vs 0.623, F#14) and inferiority on every transfer test
(F#15, F#18, F#30).

**RQ2 (screening sufficiency for real-time selection).** Yes, trivially at the
wired portfolio size: GBT screening plus HiGHS selection runs in milliseconds
(H3, 4.7 ms), and the layered guards (structural filter, MILP constraints, DAE
integration with a degraded-mode ladder) contained every screening error to a
bounded economic cost rather than an infeasible action — zero safety-class
violations across 2,000 runs (E9 count class), harm limited to 3.9% of episodes
with magnitude captured in the paired ΔR itself.

**RQ3 (end-to-end cycle within budget).** The compute-time budget is met with
orders-of-magnitude margin — the full decision cycle executes in well under one
second of wall-clock against the 60 s target — but this is a *compute-latency*
result, not a validated *production-latency* one: the 0.5 h observation grid and
simulation-time execution mean the deployed 60 s cycle at production sampling
rates is not adjudicable here and is reported as future work (§7.6). The binding
real-time constraint in this system is not compute but *information*: detection
delay (0.5–3.0 h measured) and the observation grid dominate the decision
timeline, and §7.3 shows even these are not always costs.

**RQ4 (resilience improvement and its structure).** ΔR = 0.2438 [0.2368, 0.2511]
uncapped and 0.1739 [0.1675, 0.1803] under a pessimistic purchased-copra market
(φ = 0.3), both clearing the 0.15 target on the CI lower bound (F#24, F#28);
TTR₈₀ falls 57.7% [55.2, 60.2] as a floor estimate (F#26). The dose–response
structure is monotone-increasing uncapped and plateauing under φ = 0.3; the
pre-registered inverted-U did not appear and its absence was traced to the
market-availability assumption (F#25) — discussed as a limitation in §7.6.

**RQ5 (economic translation).** ₱86.3–100.7 M/yr central estimates at [est.]
prices and frequencies, ±30% price bands, payback < 2 months against indicative
CAPEX — with the explicit caveat that the single parameter freq_D4 carries 54%
of the total and heads the verification register (F#29). The economic claim is
conditional and machine-gated, not asserted.

## 7.2 Why topology adaptation delivers: the decision-conditionality mechanism

The through-line of the results is one empirical regularity observed three
independent times in three different decision domains:

1. **Option activation** (F#5): the always-on crude bypass *harms* short refine
   outages and rescues long ones, with a ~60 h crossover — option value is
   conditional on disruption duration.
2. **Screening information** (F#13): a screen with oracle duration information
   captures 0.868 of value variance; deployable state-only information captures
   0.623 — the conditioning variable is worth a quarter of the variance.
3. **Continuous draw policy** (F#20): capacity-greedy inventory deployment beats
   passive operation under unit failures and *loses* under supply disruptions —
   even the non-topological policy is disruption-conditional.

A static twin cannot condition on any of these because it cannot re-decide. The
RDT's measured advantage is therefore not attributable to any single clever
component; it is the compounding of conditional decisions made repeatedly as the
disruption reveals itself. The sharpest single evidence is F#19: the recurrent
closed loop (ΔR = 0.190 against the passive baseline) *outperformed the one-shot
perfect-foresight oracle* (0.187). Perfect information applied once is worth less
than imperfect information applied repeatedly with reversibility — recurrence
converts prediction error from a permanent cost into a transient one. To our
knowledge no published digital-twin evaluation makes this comparison; §7.4
proposes it as a standard.

A second mechanism deserves emphasis because it inverts an intuition:
**detection delay was not a net cost** (F#22, +0.010 vs the assumed-1 h arm).
Under a hoard-then-deploy continuous policy, hours spent undetected are hours of
bridge-stock accumulation. The general statement: the cost of detection latency
is a property of the *policy it gates*, not of the detector — a design coupling
absent from the detection literature's delay-minimization framing.

## 7.3 Where the advantage thins: the honest strata

The category structure is not uniform and the weak strata are diagnostic.

**D3 (single-unit failures), ΔR = 0.140, harm 14.2%.** Unit failures are largely
*schedulable*: the hoard→deploy static policy alone reaches R = 0.876, leaving
topology only 0.12 of headroom, and the residual harm concentrates in
short-outage crude activations — the F#5 crossover crossed blindly because
duration is unobservable (F#13). The addressable fix is not a better learner but
better *information*: any duration estimate (repair-crew ETA, failure-mode
classification) would move the screen toward the 0.868 oracle bound. This is an
instrumentation-and-workflow recommendation, not a modeling one, and it is
carried into the deployment pathway.

**D8 (combined disruptions), TTR₈₀ reduction 24.2% in-stratum.** Long-duration
combined events (median static TTR 438.8 h) recover slowly under any policy;
the RDT's absolute gain (≈ 99 h) is large but the relative endpoint misses the
30% bar in-stratum. Reported alongside the pooled PASS rather than averaged
away (F#26), this stratum defines the frontier: when everything is disrupted at
once, routing headroom itself is scarce — consistent with the compression limb
of the predicted inverted-U that the sampled severity range could not otherwise
exhibit.

## 7.4 Methodological contributions

Four protocol-level results generalize beyond this plant.

**(i) Comparator symmetry dominates comparator strength** (F#21). Strengthening
the static baseline while leaving the RDT arm on an inferior continuous policy
produced a formal false negative (ΔR = 0.117, CI excluding neither bound) that
symmetric arms reversed to 0.241. Evaluations of prescriptive twins that bolt a
strong baseline under only the comparator will *understate* adaptive systems.
Proposed rule: every non-topological policy improvement granted to the baseline
must be granted to the treated arm.

**(ii) The recurrent-vs-oracle comparison** (F#19) as a standard diagnostic: if
a closed loop cannot beat its own one-shot oracle, recurrence is adding nothing
and the architecture is over-built.

**(iii) Pre-registration catches model artifacts, not just analyst bias**
(F#23, F#25). The frozen analysis predicted an inverted-U; its absence in the
frozen dose–response output was the anomaly that exposed the uncapped-purchase
unrealism *before* a reviewer could. The φ-curve reporting rule (never a scalar
for D1/D8) is the direct product.

**(iv) The layered screening pattern** — structural filter → learned surrogate
→ exact MILP → DAE verification — decouples system performance from learner
performance. Finding #18's decoupling is what let the GAT question resolve
negatively (F#30) at zero cost to the headline claims. The pattern transfers to
any real-time discrete decision over a physics-constrained network.

To these we add the integrity infrastructure (F#29): a provenance ledger with a
code-sync CI gate and a strict manuscript gate. It converts §9.2 from a
discipline into a machine-checkable condition.

## 7.5 The N2 negative result: a scale floor, stated plainly

The generalization-onset experiment (F#30) falsifies, at every scale reachable
in this thesis, the hypothesis that graph attention transfers topology-change
value to unseen options: transfer R² is negative at every training diversity
k ∈ {3..6}, *worsens* with k (median summary robust to the known
zero-variance-denominator artifact), never exceeds the flat baseline, and
carries no rank signal (ρ ≈ 0). Mechanistically, the ΔG channel learns option
*identity* where transfer requires option *physics* (F#15); descriptive edge
features (schema v1) help a tree model split directly on them but are diluted
through message passing at 10³-record scale.

Three qualifications keep this honest in both directions. First, this is a
*scale floor*, not an impossibility claim: the lifecycle's full library
(10⁴–10⁵ option-scenario examples, more wired options) is the untested regime,
and the published curve is an invitation with a baseline attached. Second, the
result is architecture-specific to the tested family (GATv2, 2–4 layers,
endpoint readout); pretraining, physics-informed losses, or relational
inductive biases tied to conservation structure are untested. Third — and this
is the constructive reading — the flat model's monotone improvement with
physics features (F#18) suggests the productive research direction at small
scale is *feature semantics*, not architecture.

## 7.6 Limitations

**Simulation-only validation** (Risk R8, standing). All 2,000 + 1,000 campaign
runs execute against the physics forward model; every dataset row carries the
SYNTHETIC label. The strong-baseline design, pre-registration, seeds-and-
provenance reproducibility, and the deployment pathway are the mitigations; a
plant pilot is future work, not a claim.

**Market availability is severity-constant.** φ = 0.3 is a single [verify]
number applied uniformly; real post-typhoon copra markets plausibly tighten
*with* severity, which would bend the φ = 0.3 plateau into the predicted
inverted-U and reduce D1/D8 tails further. Implementing φ(sev) is a scenario-
model change flagged in the register — until then, the φ-curve brackets, not
resolves, the tail.

**The comparator family is fixed-schedule.** The strong static twin selects
among four onset-aware schedules with oracle onset; a receding-horizon
continuous optimizer (MPC-lite) on fixed topology is the one stronger causal
comparator not yet built. Given that hoard→deploy already dominates its family
in ≥ 90% of scenarios and the RDT beats it with every informational
disadvantage, the expected erosion is bounded but nonzero — it is named future
work rather than assumed away.

**Detection at 0.5 h grid.** Delay medians sit at the grid floor for step-class
disruptions; production sampling (minutes) is where the 60 s cycle claim lives.

**Economic parameters.** 0/30 verified as of this draft; the strict gate is red
by design. freq_D4 (54% of E11) and φ head the worklist (F#29).

**Scope.** One plant archetype (ICPC), four primary disruption categories
(D2/D5/D6/D7 secondary sweep pending). The seven reconfiguration options modeled
in the compiler are a deliberate subset of the 19-edge candidate superstructure,
not an implementation ceiling: they were selected to span the full value
structure the screen must learn — rescue options (solar-train, nut-sale, wet-
route), a harmful-by-default option (crude-bypass below its ~60 h duration
crossover, F#5), and near-zero options (shell-boiler), with the resulting
option–disruption value matrix (F#17, Figure F8) confirming the coverage.
Extending the compiler to the remaining candidate edges is mechanical — each adds
its flow terms, capacity constraint, and HAZOP exclusions through the same
auto-derivation path — and would raise the oracle ΔR ceiling without changing the
architecture. Breadth claims are bounded to the demonstrated set accordingly.

## 7.7 Implications

**For the digital-twin literature:** topology as a runtime state variable is
architecturally cheap — 3.1 ms compilation against a 40 s budget — once the
model graph is data rather than compiled structure. The barrier the §3.1
literature treats as definitional is an implementation choice.

**For Philippine coconut processing:** the measured 17–24 percentage points of
72-hour resilience translate to ₱86–101 M/yr [est.] for a reference-scale
complex, and the deployment prerequisites surfaced by this work are concrete
and modest: the six-channel observation set (with the oil-flow lesson of F#22
— observability design precedes analytics), operator-executed line-ups under
advisory-mode recommendations, and duration estimates for unit failures as the
single highest-value information upgrade (§7.3).

**For GNN-in-PSE research:** a documented negative with paired baselines,
controls, and a scale floor is offered as a benchmark to beat — the open-source
release ships the library generator, splits, and both models.

## 7.8 Future work

Ordered by value density: (1) φ(severity)-correlated availability — one scenario-
model change that simultaneously realism-hardens the D1/D8 tails and tests the
inverted-U; (2) MPC-lite adaptive static comparator — closes the last baseline
objection; (3) duration-estimate integration into the screen — targets the
0.245 information gap and the D3 harm stratum directly; (4) secondary disruption
sweep (D2/D5/D6/D7, 400 runs, pre-registered); (5) the 10⁴–10⁵ option-scenario
library extending the N2 curve rightward; (6) hardware-in-the-loop latency and
the plant pilot per the deployment pathway.

---
*The chapter's single-sentence summary: resilience decisions in this plant are
disruption-conditional in every domain measured — options, information, and
draw policy — and the quantified value of a digital twin that can re-decide is
17–24 percentage points of 72-hour throughput, robust to comparator hardening,
detection realism, and a 3× market-availability haircut.*
