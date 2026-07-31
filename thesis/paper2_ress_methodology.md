# Evaluating Prescriptive Digital Twins for Resilience: Six Protocols, and What They Reject

*Paper 2 draft v1, 2026-07-13. Target: Reliability Engineering & System Safety.
Every quantitative claim traces to a run recorded in the public repository. The
register of what was tested and what failed is `thesis/reframe_status.md`.*

---

## Abstract

Prescriptive digital twins are increasingly proposed as resilience
infrastructure: systems that observe a disruption and recommend a response.
Whether such a system works is an empirical question, and the answer depends
entirely on how it is evaluated. We argue that evaluation practice for
prescriptive systems is immature in ways that produce confidently wrong answers,
and we develop six protocols that detect the specific failures. Each is
demonstrated on a reactive digital twin that reconfigures the topology of an
integrated coconut processing complex under typhoon-calibrated disruption, across
2,000 pre-registered paired Monte-Carlo scenarios. The protocols are: enforce
comparator symmetry, because granting the baseline an improvement withheld from
the treated arm manufactured a false negative in our own study, 0.117 against a
true 0.241 on identical scenarios; benchmark a closed loop against its own
one-shot perfect-foresight oracle, because a loop that cannot beat it is not
earning its complexity; bound the continuous-control alternative rather than
arguing about it, which here widened rather than narrowed the measured advantage,
0.294 against a headline 0.244; pre-register, because the frozen analysis caught
an unphysical modeling assumption rather than merely constraining the analyst;
model re-initialization honestly, because hot-starting newly activated units
understated a decision threshold three- to fourfold; and evaluate a detector
inside the policy it gates, because detection delay proved net beneficial under a
hoarding policy. We then turn the protocols on ourselves: four mechanistic explanations we
proposed for the system's behaviour were falsified before publication, and we
report them. The resilience result, a 0.244 improvement in the 72-hour resilience
integral and a 57.7% reduction in time to 80% recovery, is the worked example
rather than the contribution.

**Keywords:** resilience evaluation; prescriptive analytics; digital twin;
comparator design; pre-registration; process systems.

---

## 1. Introduction

### 1.1 The evaluation problem

A prescriptive system earns its place by changing decisions. That makes the
central claim about any such system comparative: the plant does better *with* it
than *without* it. Comparative claims are only as good as the comparison, and the
comparison is a design artifact chosen by the same people who built the system
being evaluated.

This is not a hypothetical concern. In the course of the study reported here, an
apparently reasonable evaluation design produced a resilience gain of 0.117 with
a confidence interval that would have been reported as a weak positive. The same
system, on the same scenarios, measured 0.241 once a single asymmetry in the
comparison was corrected. Nothing about the flawed design announced itself. It
looked like an honest, even conservative, evaluation, and it was wrong by a
factor of two.

Resilience evaluation is where this matters most, because the decisions at stake
are infrastructure decisions. A system that appears to deliver resilience it does
not deliver diverts investment from measures that would. In the setting studied
here, an agro-industrial complex serving smallholder coconut farmers in the
Philippine typhoon corridor, that misallocation has a human cost.

### 1.2 What this paper contributes

We do not offer a new resilience metric or a new optimization formulation. We
offer six evaluation protocols, each addressing a failure mode we encountered and
measured, and each stated so that it transfers to any prescriptive system
evaluated against a baseline.

The protocols are demonstrated on a reactive digital twin (RDT) that reconfigures
process topology at runtime under supply and utility disruption. That system is
described only to the depth needed to make the demonstrations legible; its own
performance is reported in Section 5 as a worked example.

Section 6 does something less usual. Having proposed the protocols, we apply them
to four mechanistic explanations we ourselves advanced for the system's behaviour.
All four were rejected. We report the rejections in full, because a methodology
whose only evidence is the claims it confirmed has not been tested.

## 2. Related work on evaluating prescriptive systems

Resilience quantification is well developed. Metrics based on the recovery-curve
integral descend from Bruneau et al. (2003), and reviews by Hosseini et al. (2016)
and Yodo and Wang (2016) survey the space. In process systems specifically,
Chrisandina et al. (2024, 2025) develop resilience-aware design metrics including
a combined flexibility-resilience index expressing the likelihood that a system
remains feasible under an uncertainty and disruption set.

This literature answers *what to measure*. It says comparatively little about
*what to measure against*, which is the subject of this paper. The gap is not
peculiar to resilience engineering. Evaluation practice in adjacent prescriptive
domains, including online network reconfiguration in power distribution and
learning-based control, generally reports performance against a nominal or
rule-based baseline without examining whether that baseline was granted the same
advantages as the treated system.

Two literatures inform specific protocols. The methodological argument for
pre-registration originates in the empirical sciences as a guard against analyst
degrees of freedom; Section 4.4 reports a different function, detection of model
error. The practice of bounding an unbuilt alternative rather than constructing it
is standard in optimization, where relaxations and oracles are routine, and
Section 4.3 applies it to comparator design.

## 3. The demonstration system

The system under evaluation is a reactive digital twin for an integrated coconut
processing complex: seven unit operations, four utility networks, four saleable
products. Unlike prescriptive twins that optimize setpoints on a fixed flowsheet,
it treats the process topology as a runtime decision variable, activating and
deactivating stream routings as a disruption unfolds. Four engines compose in a
recurrent loop: hybrid Bayesian online change-point detection with a CUSUM drift
arm; a graph-attention surrogate that screens candidate reconfigurations; a
mixed-integer linear program that selects among screened candidates under
constraints derived from the process graph; and an index-1 differential-algebraic
model that verifies the selected transition is dynamically reachable.

Disruptions are sampled by Latin hypercube over eight categories, with severity
and duration ranges calibrated to Philippine tropical-cyclone conditions:
feedstock supply interruption, quality degradation, unit failure, utility outage,
logistics interruption, cascading failure, drought, and combined events. All data
are synthetic, generated by the physics forward model and marked as such at the
row level. No proprietary plant data are used.

Resilience is the normalized area under the recovery curve on a margin-weighted
value basis over a 72-hour window, and the comparative quantity throughout is the
paired difference on identical disruption realizations under common random
numbers.

## 4. Six protocols

### 4.1 Enforce comparator symmetry

**The failure mode.** Hardening an evaluation usually means strengthening the
baseline. The instinct is correct and incomplete. If a non-treatment improvement
is granted to the baseline and withheld from the treated arm, the comparison
measures the difference in that improvement rather than the effect of the
treatment.

**What we measured.** Our static comparator was strengthened from a passive
policy to an onset-scheduled policy with oracle knowledge of disruption onset.
Against that hardened baseline the reactive twin scored 0.117, CI [0.093, 0.142].
The result was a formal positive but weak enough to reject the practical claim.
The reactive arm, however, was still running an inferior continuous inventory
policy with pre-drawn buffers. Granting both arms the same continuous policy, and
leaving the baseline its oracle-onset advantage, gave 0.241, CI [0.215, 0.267] on
the same scenarios.

**The protocol.** Enumerate every improvement granted to either arm and verify it
is available to both, or that its absence is a property of the treatment rather
than of the experiment. Report the enumeration. An asymmetry that favours the
baseline is not conservative; it is a measurement of the wrong quantity.

### 4.2 Benchmark the loop against its own oracle

**The failure mode.** Recurrent architectures are justified by the claim that
re-deciding is better than deciding once. The claim is rarely tested, and it is
not free: a loop costs implementation complexity, compute, and failure modes.

**The diagnostic.** Run the system's own action set once, at onset, with perfect
foresight of the disruption. That one-shot oracle is an upper bound on any
single-decision policy. If the recurrent loop cannot beat it, recurrence is
contributing nothing and the architecture should be collapsed.

**What we measured.** The recurrent loop scored 0.190 against the one-shot
oracle's 0.187. Recurrence wins, but by 0.003. That thin margin is itself the
finding: imperfect information applied repeatedly slightly exceeded perfect
information applied once, and a system with a marginally different option set
could easily fall on the other side. Reporting the margin, rather than the
existence of a gain, tells a reader how much of the architecture is load-bearing.

### 4.3 Bound the alternative you did not build

**The failure mode.** Every prescriptive-system evaluation attracts the objection
that some unbuilt alternative would have done as well. Building it is expensive;
arguing about it is unfalsifiable.

**The protocol.** Construct an optimistic bound on the alternative and compare
against that. Here the objection was that a receding-horizon continuous
controller might capture the gain without any topology change. Rather than build
one, we formed the clairvoyant envelope over the two continuous draw regimes,
taking the better regime at every instant with perfect foresight and free
switching. That dominates any causal controller over the same action set.

**What we measured.** The envelope is a genuine strengthening: it scores 0.666
against the realized static comparator's 0.637. The reactive twin still clears it
by 0.294, CI [0.286, 0.302]. The margin against the *stronger* comparator exceeds
the margin against the weaker one, which is the signature of an advantage that
does not lie on the axis the alternative operates on.

**The general form.** A bound that the treatment survives converts an open
objection into a closed inequality at a fraction of the cost of building the
alternative. A bound the treatment fails is equally informative and much cheaper
to learn.

### 4.4 Pre-register, and expect to catch model errors

**The failure mode.** Pre-registration is normally motivated by analyst degrees of
freedom. In simulation studies the analyst and the modeler are the same person and
the data are regenerable, which is often taken to make pre-registration
ceremonial.

**What we measured.** The frozen analysis plan predicted an inverted-U
dose-response, with resilience gain peaking at intermediate severity. The
prediction failed in the frozen output. Because the prediction had been committed
in advance, its absence was an anomaly requiring explanation rather than a curve
to be described. The explanation was a modeling error: an uncapped purchased-input
market that, at extreme regional disruption, sourced replacement feedstock from a
market the same disruption had destroyed. Introducing a market-availability
parameter recovered a physically sensible response and changed the headline result
under constrained availability from 0.244 to 0.174.

**The protocol.** Pre-register predictions, not only endpoints. A prediction that
fails is the cheapest available detector of model error, and in simulation studies
model error is the dominant failure mode rather than analyst bias.

### 4.5 Model re-initialization honestly

**The failure mode.** When a prescriptive system activates equipment, the
simulation must decide what state that equipment starts in. This is normally an
implementation detail settled by convenience.

**What we measured.** Our topology compiler initialized newly activated dryer
compartments at inlet moisture, so a newly commissioned train contributed output
as soon as flow reached it. Replacing this with a commissioning contract, in which
availability ramps from zero with a time constant set by vessel residence, raised
the breakeven disruption duration for the affected option from 4.3 hours to 12.2
hours at one residence setting and from 3.7 to 15.6 at another. The decision
threshold moved by a factor of three to four, and the sign of its dependence on
residence time reversed.

**The protocol.** State the re-initialization contract explicitly and test the
decision's sensitivity to it. A twin that hot-starts activated equipment will
recommend actions at disruption durations where the physical plant would lose
money. This is not a numerical detail; it determines whether the recommendation is
correct.

### 4.6 Evaluate a detector inside the policy it gates

**The failure mode.** Detection performance is conventionally reported against
delay and false-alarm objectives, evaluated in isolation from the response the
detection triggers.

**What we measured.** Charging the loop its measured detection delays, rather than
granting an assumed one-hour detection, *improved* the paired outcome by 0.010.
The continuous policy in force was hoard-then-deploy, under which hours spent
undetected are hours of bridge-stock accumulation that the eventual
reconfiguration then spends to better effect.

**The protocol.** The cost of detection latency is a property of the policy the
detector gates, not of the detector. A detector optimized against a delay
objective in isolation can be optimized against the wrong criterion. Report
detection performance and end-to-end performance together.

## 5. The worked example

Applying all six protocols, the reactive digital twin improves the 72-hour
resilience integral by ΔR = 0.244, CI [0.237, 0.251], over 2,000 pre-registered
paired scenarios against a hardened symmetric comparator, and by 0.294,
CI [0.286, 0.302], against the clairvoyant continuous-control bound. Under a
pessimistic purchased-input market the gain is 0.174, CI [0.168, 0.180]. Time to
80% recovery falls 57.7%, CI [55.2, 60.2], reported as a floor estimate because
excluded episodes are those in which the treated arm never dropped below the
threshold. Harmful reconfigurations occur in 3.9% of episodes against a 5%
acceptance bound, with zero safety-class constraint violations across the
campaign. Selection latency is 4.7 ms and topology recompilation 3.1 ms, both
orders of magnitude inside the cycle budget.

We report one negative result about the system itself. Graph-attention screening
does not generalize to reconfigurations absent from training: transfer is negative
at every training-diversity level examined, degrades as diversity grows, and never
exceeds a flat gradient-boosted baseline on identical splits. The layered
architecture is what makes this non-blocking, since the screening slot is filled
by the tabular model and system performance does not depend on the graph model.

## 6. Turning the protocols on ourselves

A methodology demonstrated only on claims it confirmed has not been tested. We
therefore report four mechanistic explanations we advanced for the system's
conditional behaviour, all of which these protocols rejected before publication.

The system exhibits options that are net harmful on short disruptions and
valuable on long ones, with breakevens between 33 and 69 hours. We proposed that
this arises from transition dynamics: reconfiguring a process plant takes hours,
comparable to the disruption itself, so an option is worth taking only if the
disruption outlasts the transition. The proposal yields a closed-form breakeven,
predicts that it moves with transition time at unit slope, and distinguishes
process reconfiguration from power-network reconfiguration where switching is
instantaneous. It was an attractive claim and we tested it four ways.

Sweeping the dominant residence time against control-input options gave a slope of
approximately zero, because those options bypass the dryer and its residence is
not their transition time. Sweeping it against a topology option that adds dryer
capacity also gave zero, because parallel capacity addition delays a gain without
sacrificing the operating path, so the transition cost the theory requires is
absent. Introducing an explicit commissioning gate on a substitutive option again
gave zero, because the gate delays the option's effect without opening a value
gap. A separate proposal, that perishability of the stored intermediate forecloses
the buffering strategy and thereby forces reconfiguration, produced a null under
an experimental design that we subsequently found invalid: scaling initial
inventory perturbs the operating point rather than representing designed buffer
capacity.

The conclusion is that the conditional structure in this system is economic,
arising from a standing opportunity cost set against the timing of constraint
activation, and not transitional. We report this because it is what the evidence
supports, and because the sequence demonstrates the protocols functioning as
intended: each rejection came from a falsifiable prediction stated in advance and
tested against data that could have gone the other way.

## 7. Discussion

**On what generalizes.** None of the six protocols is specific to process
engineering, to digital twins, or to resilience. Each addresses a failure mode
that arises whenever a prescriptive system is compared against a baseline the
evaluator also designed. We expect them to transfer to prescriptive systems in
power dispatch, water network operation, and supply-chain control, and we note
that in each of those domains the reported evaluations we surveyed satisfy some
protocols and not others.

**On the cost of the protocols.** Five of the six are cheap. Comparator symmetry
is an enumeration. The oracle diagnostic is one additional campaign arm. The
clairvoyant bound is two arms and an envelope. Pre-registration is a commit hash.
Detection-inside-policy is a choice of which arm to charge. Only the
re-initialization protocol required model surgery, and it returned the largest
single correction.

**On negative results.** Two of the results reported here are negative: the
graph-attention screen does not generalize, and our own mechanistic explanation
does not hold. Both were retained because the protocols that produced them are the
paper's subject, and a reader is entitled to see them working against the authors'
interest.

## 8. Limitations

All results derive from a physics forward model; no plant data enter any claim,
and a field trial is future work rather than a completed validation. The
demonstration covers one plant archetype and seven reconfiguration options chosen
to span the value classes the screen must learn. The clairvoyant bound covers the
two-regime draw action set and does not bound a continuous-modulation controller.
Economic figures are indicative, resting on planning-grade prices and disruption
frequencies tracked in a provenance ledger whose strict gate fails by design until
they are verified against Philippine public sources; no unverified number is
load-bearing for any claim in this paper. Finally, the protocols are demonstrated
rather than proven: we show that each detected a real failure in one study, not
that each is necessary or sufficient in general.

## 9. Conclusions

Prescriptive systems are evaluated by comparison, and the comparison is designed
by the evaluator. We have shown, on a single study, that plausible evaluation
choices produced an effect estimate wrong by a factor of two, a decision threshold
wrong by a factor of three, and a detection result with the wrong sign. Six
protocols detected each of these, and rejected four of our own mechanistic claims
besides. The resilience result they support, a 0.244 improvement in the 72-hour
resilience integral for runtime topology reconfiguration under typhoon-calibrated
disruption, is stated with more confidence than it would otherwise deserve,
precisely because the protocols were given the opportunity to reject it.

## Data and code availability

The complete simulator, disruption library, analysis pipeline, and every
experiment reported here, including the falsified ones, are publicly available at
https://github.com/beebzy-droid/rdt-thesis3 behind a one-command reproducibility
harness with a determinism-verified rebuild path.
