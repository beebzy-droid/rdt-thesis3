# Chapter 6 — RESULTS

*Draft v1, 2026-07-04. All numbers trace to FINDINGS.md entries (cited as F#n) and
repository commits. Bracketed [est.]/[verify] flags mark planning-grade parameters
excluded from citable claims until sourced (§9.2 integrity rule). Figures F1–F8
regenerate from `scripts/make_figures.py`.*

## 6.1 Simulator verification and reference plant behavior

The compiled plant model passed the Phase-1 verification gates before any learning
or optimization work began. The graph-to-DAE compiler reproduces the hand-coded
reference model to a maximum state deviation of 1.37×10⁻¹⁴ over a 30-day nominal
trajectory (C1 equivalence, machine precision), and compiles a new topology in
3.1 ms against the 40 s §2.2 budget — a 10⁴ margin that makes per-cycle topology
switching computationally free at plant scale (F#8-era commits). Mass-balance
closure over 30-day nominal runs is below the 0.5% gate; the sinks-accounting
identity holds by construction in the compiler's flow graph.

Two structural results of the verification phase shaped everything downstream.
First, the Eq. 2.11 rank condition proved vacuous on the ICPC superstructure —
every candidate subgraph satisfies it — and was replaced by a degree/reachability
structural filter (F#1); the rank test is retained only as a consistency assertion.
Second, the carbonizer was found 573%-loaded in the nominal flowsheet as specified,
forcing shell sale to be promoted to a nominal (not candidate) route (F#2). Both
are reported because they falsify the assumption that the published reference
specification (Table 5.1) is internally consistent as an operating plant; the
model of record is the corrected flowsheet.

The resilience metric is computed on a **margin-weighted value basis** (₱/hr),
not mass, after a D2 blindness demonstration: a mass-basis R is numerically
insensitive to quality degradation that destroys most of the product's value
(F#3). Product value weights (VCO 200, crude 140, meal 22, char 32, concentrate
100, shell 8 ₱/kg) are [est.; verify: PCA price monitors] and enter all ΔR values
as a fixed vector — the ±30% price sensitivity of §6.8 bounds their influence.

## 6.2 Screening layer: learnability and the small-k null

The learned screening question was posed as three nested experiments on the
labeled option–scenario library (1,120 records, seven options, four disruption
categories, switch-at-decision protocol per F#16).

**In-distribution learnability.** A gradient-boosted regressor on oracle-informed
features (including disruption duration and severity — future information at
decision time) reaches R² = 0.868; restricted to the deployable state-only
feature set it reaches R² = 0.623 (F#10, F#13). The gap between these two numbers
is the measured value of disruption characterization: duration is the dominant
unobservable, and its absence is the direct cause of the D3 harm stratum in §6.6.

**Graph model at parity.** A GATv2-faithful prototype (edge-featured dynamic
attention, ΔG edge channel, block-diagonal batching) scores R² = 0.644 ± 0.177
across scenario-disjoint folds — parity with the flat state-only baseline
(0.623 ± 0.159), seed-stable (fold-0 spread 0.636 ± 0.007, n = 3) (F#14). At
1,120 records over a fixed option set, relational structure adds nothing that a
flat model cannot extract; this is the expected regime per the reframing of F#10.

**The small-k null (leave-one-option-out).** No model — GAT, flat GBT, or an
option-identity-blind control — generalizes to topology changes absent from
training at k ≤ 7 options. Mean transfer R² over informative rotations:
GAT −5.71, flat −0.71, blind −1.00 (F#15, F#18). The controls carry the
information: apparent transfer on one rotation was exposed as a state confound
(the blind model, with zero option identity, matched it at ρ = 0.876), and the
GAT's below-blind performance on two rotations shows its ΔG channel encodes
option *identity* rather than option *physics*. Physics-descriptive edge features
(schema v1) improved the flat model's transfer monotonically (k = 3→7:
−2.12→−0.71) while the GAT worsened (−2.92→−5.71): at this data scale, high-
capacity relational models overfit identity harder.

The consequence is the **strategic decoupling** (F#18) that defines the system
architecture reported in this thesis: the operational screening slot is filled by
the physics-featurized GBT, which dominates every measured axis; the GAT
generalization claim (N2) is reposed as a *generalization-onset scaling question*
— at what option diversity k does ΔG-transfer emerge? — with k = 3 and k = 7
establishing the null (left) side of that curve. The layered architecture
(structural filter → learned screen → exact MILP → DAE verification) is
indifferent to which learner fills the screening slot; system-level resilience
results (§6.5–6.7) therefore do not gate on N2.

## 6.3 Decision layer: MILP selection

The HiGHS selector over the seven-option portfolio (simultaneity N_max = 3,
seed exclusion pairs auto-derived from the graph, activation threshold with
hysteresis) solves in 4.7 ms median — 10³ under the §2.3 5 s budget (H3 ✓).
Exclusion honoring and n-max saturation are CI-gated unit tests. At K = 7 the
problem is trivially small; the H3 latency claim at K ≤ 50 was verified on
synthetic candidate sets during Phase-3 development and is not the binding
resource anywhere in the decision cycle.

## 6.4 Detection layer

The disruption detector is a **hybrid**: the Eq. 2.14–2.15 BOCPD run-length
posterior (Normal-Inverse-Gamma conjugate channels, constant hazard λ = 500,
trigger P(r ≤ 4) > 0.85) fused with a two-sided tabular CUSUM (k = 0.5σ,
h = 12σ) over six z-scored observation channels at the 0.5 h simulation grid.
Three defects were found and fixed en route, each generalizing beyond this plant
(F#22): (i) slow supply ramps *structurally* evade run-length triggers (48% miss
on D1 for pure BOCPD) — drift detection is a distinct capability class, supplied
by the CUSUM arm; (ii) quality disruptions were 98%-missed not by the detector
but by the *observation set* — invisible until a press-oil-flow channel existed
(observability design precedes detector design; carried into the §5.5.2
instrumentation checklist); (iii) an 11.4/30 d false-alarm rate traced to
calibrating on the plant's own settling transient, eliminated by steady-state
warm start.

Benchmark at the locked configuration (E10 ✓, Figure F6): false alarms
0.80/30 d (≤ 1 target); detection delay median 0.5 h (grid floor) for step-class
disruptions (D2/D3/D4), 2.5 h for slow-ramp D1, 3.0 h for combined D8; miss rate
0% in all categories; pre-onset false alarms ≤ 0.12/run. The 0.5 h observation
grid floors measurable delay; the 60 s lifecycle target applies at production
sampling rates and is not adjudicable in this simulation. **H6 is therefore
reported as not tested at production conditions**: the compute-time budget is met
with a >10³ margin (the full decision cycle executes in well under one second of
wall-clock), but the end-to-end latency claim at production sampling (minutes,
not the 0.5 h simulation grid) requires deployment hardware and is future work
(§7.6). No resilience result depends on H6.

## 6.5 Closed-loop protocol and comparator hardening

The headline resilience comparison required five comparator iterations, and the
sequence is itself a methodological result (Figure F7; F#19–F#21). Against a
passive static twin the recurrent RDT loop scored ΔR = 0.190 [0.169, 0.211] —
and, notably, *above* the one-shot perfect-foresight oracle (0.187): recurrence
plus reversibility beats one-shot optimality because the loop composes options
sequentially and unwinds errors (F#19, confirming the F#13 prediction). Comparator
strengthening followed: a capacity-greedy "strong" static proved *worse* than
passive by −0.033 pooled — aggressive buffer deployment burns bridge stock
exactly when supply disruptions need it held, a third independent instance of
decision-conditionality (F#20). The onset-scheduled policy family (hoard→deploy
at oracle onset) then produced a **formal false negative**: ΔR = 0.117
[0.093, 0.142] — but against an RDT arm still running capacity-greedy draws with
pre-burned buffers. Restoring §5.4.2 arm symmetry (RDT rides the winning
hoard→deploy schedule under its own 1 h detection; the static comparator keeps
its oracle-onset advantage) gave ΔR = 0.241 [0.215, 0.267], identical against
the hindsight best-of-four selector (F#21). The lesson, proposed as a protocol
requirement for prescriptive-twin evaluation: **comparator strength without arm
symmetry produces false negatives** — the 0.117 would have wrongly killed H4.

## 6.6 Full-scale campaign: resilience improvement (H4)

The pre-registered campaign (analysis endpoints frozen at commit before
execution; F#23) ran 2,000 paired scenarios — four categories × 500, fresh seed
disjoint from all training and pilot draws — with measured hybrid detection
gating both the continuous-regime switch and topology decisions, against the
oracle-onset strong static comparator (Figures F1–F3).

**H4 is adjudicated PASS and φ-robust** (F#24, F#28):

| Market availability | pooled ΔR | 95% CI | formal (CI > 0.10) | target (CI > 0.15) |
|---|---|---|---|---|
| φ = ∞ (uncapped purchase) | 0.2438 | [0.2368, 0.2511] | ✓ (2.4×) | ✓ |
| φ = 0.3 [est.; verify] | 0.1739 | [0.1675, 0.1803] | ✓ (1.7×) | ✓ |

Wilcoxon signed-rank p ≈ 10⁻³¹⁰ (uncapped). Per-category means (uncapped →
φ = 0.3): D1 0.306 → 0.162; D3 0.140 (no purchase route exposure); D4 0.255;
D8 0.275 → 0.139. Secondary endpoints: harm fraction P(ΔR < −0.01) = 3.9%
pooled (< 5% discussion threshold, E9 ✓), concentrated in D3 (14.2%) where the
state-only screen cannot observe outage duration (§6.2); reconfiguration count
median 2 per episode (plausibility gate ≤ 12 ✓); degraded-mode numerics ladder
fired 0.126×/episode on D3 and 0 elsewhere.

The dose–response structure answers RQ4 with a caveat that became Finding #25:
uncapped, ΔR rises monotonically with severity (D1: 0.196 → 0.426 across
quintiles) because the purchased-copra route follows the deficit without market
limit — an unrealistic assumption during regional disruption. Capped at φ = 0.3
the curve *plateaus* (D1: 0.155–0.165) rather than inverting; the predicted
inverted-U requires severity-correlated availability φ(sev), which is follow-on
work. The standing manuscript rule: **D1/D8 resilience gains are reported as a
function of φ, never as a scalar.**

## 6.7 Recovery dynamics (H5)

Paired time-to-80%-recovery used the Amendment-A1 supplement (static-arm TTR₈₀
on identical seeds; amendment flagged before campaign data existed) with an
integrity cross-check — R_static agreement between independent passes was exact
(0.00×10⁰ maximum deviation over 2,000 scenarios). **H5 is adjudicated PASS**
(F#26, Figure F4):

- Mean TTR₈₀ reduction **57.7%, 95% CI [55.2%, 60.2%]**, n = 1,193
  impaired-under-static episodes — target (≥ 30%) cleared at 1.8× on the CI
  lower bound.
- The estimate is a **floor**: 254 episodes where the static twin never recovers
  within 30 days but the RDT does are excluded (undefined ratio; all favorable);
  the adverse asymmetry count is zero; the RDT is never-impaired in 373 episodes
  against 41 for the static twin.
- Per category: D4 75.0%, D1 56.0%, D3 50.0%, D8 24.2%. The D8 stratum
  (long-duration combined events; median TTR 438.8 → 340.1 h) is below the 30%
  target in-stratum — reported alongside the pooled endpoint rather than
  averaged away.

A metric note (F#21): R > 1 occurs legitimately (e.g., D4 mean R_RDT = 1.049)
when hoarded pre-window inventory deploys at capacity inside the recovery
window; Eq. 2.16 is uncapped by design and both arms play the same inventory
game, so paired ΔR is unaffected.

## 6.8 Economic translation (E11)

At V₀ ≈ ₱470,000/hr nominal value flow [est.; from the model's price vector]
over the 72 h assessment window, with episode frequencies of 2/4/6/1 per year
for D1/D3/D4/D8 [est.; verify: PAGASA cyclone climatology, plant reliability
records, DOE/NGCP interruption indices]:

| Market assumption | annualized benefit | ±30% price band |
|---|---|---|
| φ = ∞ | ₱100.7 M/yr | 70.5–130.9 |
| φ = 0.3 | ₱86.3 M/yr | 60.4–112.2 |

Against an indicative deployment CAPEX of ₱5–15 M [est.] the simple payback is
under two months at central estimates. Two parameters dominate the uncertainty
and head the verification register: the **D4 utility-outage frequency** (6/yr
[est.]) alone carries 54% of the uncapped total, and the **market availability
φ** moves the total by 14%. No figure in this section is citable until its
provenance entry is closed (§9.2).

## 6.9 Hypothesis adjudication summary

| ID | Original statement | Disposition |
|---|---|---|
| H1 | GAT ≥ 90% feasibility accuracy | **Reframed** (F#14, F#18): feasibility screening is structural (filter) + GBT; GAT accuracy at prototype scale is parity-with-flat; N2 reposed as generalization-onset scaling question with the small-k null established |
| H2 | GAT impact MAPE ≤ 10% | **Reframed** with H1; deployable state-only screen R² = 0.623 with the oracle gap (0.868) quantifying the value of disruption characterization |
| H3 | MILP < 5 s, K ≤ 50 | **PASS** — 4.7 ms at K = 7; 10³ margin |
| H4 | ΔR ≥ 0.15, CI excluding 0.10 | **PASS, φ-robust** — 0.244 [0.237, 0.251] uncapped; 0.174 [0.168, 0.180] at φ = 0.3; both CIs clear the 0.15 target itself |
| H5 | TTR₈₀ reduction ≥ 30% | **PASS** — 57.7% [55.2, 60.2], floor by construction |
| H6 | cycle ≤ 60 s p95 | **Not tested at production conditions** — compute budget met with >10³ margin (cycle ≪ 1 s wall-clock); end-to-end latency at production sampling rates requires deployment hardware (§7.6), future work |

The through-line of the results is a single empirical claim instantiated three
independent ways (options F#5, screening F#13, draw policy F#20): **the value of
every resilience decision in this plant is disruption-conditional** — and a
digital twin that cannot re-decide as the disruption reveals itself leaves the
measured 17–24 percentage points of resilience on the table.

---
*Data provenance: all results derive from the physics forward-model simulator;
all datasets carry `data_class = SYNTHETIC/physics-forward-model` at row level.
No real plant data enters any number in this chapter.*
