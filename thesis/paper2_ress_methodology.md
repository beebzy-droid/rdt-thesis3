# Evaluating Prescriptive Digital Twins for Resilience: Six Protocols, and What They Reject

*Paper 2 draft v1, 2026-07-13. Target: Reliability Engineering & System Safety.
Every quantitative claim traces to a run recorded in the public repository. The
register of what was tested and what failed is `thesis/reframe_status.md`.*

---

## Abstract

Prescriptive digital twins are increasingly proposed as resilience
infrastructure: systems that observe a disruption and recommend a response.
Whether one works depends entirely on how it is evaluated. We argue that
evaluation practice for such systems is immature in ways that produce confidently
wrong answers, and develop six protocols that detect the specific failures. Each is demonstrated on a reactive
digital twin that reconfigures the topology of a coconut processing complex under
typhoon-calibrated disruption, across 2,000 pre-registered paired Monte-Carlo
scenarios. The protocols require comparator symmetry, which when violated in our
own study manufactured a false negative of 0.117 against a true 0.241;
benchmarking a closed loop against its own one-shot perfect-foresight oracle;
bounding the alternative one did not build, which here widened rather than
narrowed the measured advantage; pre-registering predictions, which caught an
unphysical modeling assumption rather than merely constraining the analyst;
modeling re-initialization honestly, since hot-starting newly activated units
understated a decision threshold three- to fourfold; and evaluating a detector
inside the policy it gates, since detection delay proved net beneficial under a
hoarding policy. Two further tests follow. We turn the protocols on ourselves,
reporting four explanations of our system's behaviour that they falsified before
publication. And we audit roughly thirty published evaluations, finding recurrence
justification and re-initialization reporting near-universally absent, and
detection and decision studied by communities that do not reference one another; a
blind two-rater subsample gives a pooled Cohen's kappa of 0.818, with
disagreements falling on degree of compliance rather than on whether a practice
was a problem. The resilience result the protocols support is
the worked example rather than the contribution.

**Keywords:** resilience evaluation; prescriptive analytics; digital twin;
comparator design; pre-registration; process systems.

---

## 1. Introduction

### 1.1 The evaluation problem

A prescriptive system earns its keep by changing decisions, which makes every
claim about one a comparative claim: the plant does better with it than without.
And a comparative claim is only ever as good as its comparison. The
uncomfortable part is who builds that comparison. It is not an external standard
handed down to the evaluator; it is a design artifact, chosen by the same people
who built the thing being evaluated, and shaped by their intuitions about what a
fair test looks like.

We learned how much room that leaves for error by getting it wrong. Partway
through the study reported here, a careful and, we thought, conservative
evaluation returned a resilience gain of 0.117. It was a positive result with a
confidence interval clear of zero, and we came close to reporting it as a modest
success. It was wrong by a factor of two. The same system, on the same
scenarios, measures 0.241 once a single asymmetry in the comparison is removed.

What unsettled us was not the size of the error but its silence. The flawed
design did not look flawed. It looked like the more rigorous choice, because it
strengthened the baseline, and strengthening the baseline is what a careful
evaluator is supposed to do.

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
peculiar to resilience engineering. We are not aware of a systematic audit of
comparator design in prescriptive-system evaluation, in this field or in adjacent
ones, and we make no claim about its prevalence. What we can report is that the
failure modes below were live in our own study, that they were not obvious in
advance, and that each changed a headline number materially.

### 2.1 What the learning community already established

We are not the first to argue that evaluation quality is a research problem. The
reinforcement-learning community has built a substantial methodological literature
on exactly this: Henderson et al. (2018) showed that seeds, hyperparameters and
codebase differences make reported results hard to interpret; Agarwal et al. (2021)
showed that point estimates over few runs mislead and argued for interval estimates
and robust aggregate statistics; Jordan et al. (2020) and Patterson et al. (2024)
develop evaluation methodology and empirical design more broadly.

Adjacent fields have supplied the harder evidence. Ferrari Dacrema et al. (2021),
extending a 2019 analysis, could reproduce twelve of twenty-six neural
recommendation papers with reasonable effort and found that eleven of those twelve
were outperformed by conceptually simple methods, in several cases because the
baselines had not been tuned. Comparable reality checks exist in metric learning
(Musgrave et al., 2020) and in time-series forecasting. The pattern is consistent
and uncomfortable: where evaluation is not disciplined, apparent progress is
partly an artifact of the comparison.

Reporting standards are the usual institutional answer. Medicine has CONSORT,
PRISMA and TRIPOD; health-economic simulation has the ISPOR-SMDM guidance; machine
learning has the NeurIPS checklist and, most recently, REFORMS (Kapoor et al.,
2024), a thirty-two-question consensus instrument for machine-learning-based
science. Resilience engineering and prescriptive decision support have no
equivalent.

### 2.2 What is different about prescriptive systems

The prior art above is overwhelmingly concerned with *statistical* validity and
*reproducibility*: how many seeds, which intervals, was the baseline tuned, can the
result be regenerated. Those questions matter here too, and we answer them.

But they are not the questions that cost us most. Four of our six protocols
concern something the existing literature does not formalize, which we will call
*decision-theoretic* validity: whether the comparison is measuring the decision the
system actually makes. A perfectly reproducible experiment with well-tuned
baselines and generous seed counts can still be asking the wrong question. It can
compare a closed loop against a baseline without ever testing whether the loop
needs to be closed. It can leave an alternative approach unbounded and merely
asserted to be worse. It can let activated equipment contribute instantly, so the
recommendation is evaluated in a world where reconfiguration is free. It can score
a detector against a delay objective that its own downstream policy contradicts.

None of those failures is statistical, and none is caught by a reproducibility
checklist. They are failures of experimental design specific to systems that
prescribe actions, and they are what this paper addresses.

### 2.3 What is new here, and what is borrowed

Not all six protocols are novel, and a paper that implied otherwise would deserve
the scepticism it received. Two are adaptations of established practice to a new
setting: pre-registration comes from the empirical sciences, and bounding an
unbuilt alternative is routine in optimization, where relaxations and oracles are
everyday tools. Comparator symmetry is, in one sense, nothing more than
experimental control, which is why its violation in our own study is the more
instructive: knowing the principle did not prevent us from breaking it.

Three we believe are new as stated. The recurrent-versus-oracle diagnostic gives
a specific, cheap test of whether recurrence in a closed loop is load-bearing.
The re-initialization protocol identifies a modeling choice normally settled by
convenience as a first-order determinant of the recommendation. And evaluating a
detector inside the policy it gates inverts the usual delay-minimization
objective, which we show can point the wrong way.

The contribution is therefore not that each protocol is unprecedented. It is that
this particular set addresses the failure modes specific to prescriptive systems,
that each is demonstrated rather than argued, and that together they were
sufficient to reject four of our own claims.

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

Resilience is the normalized area under the recovery curve,
$R(T) = T^{-1}\int_0^T P(\tau)/P_0\,d\tau$, evaluated over a 72-hour window after
onset. One modeling choice inside that definition matters enough to state: $P$ is
computed on a margin-weighted value basis rather than a mass basis. On a mass
basis a disruption that halves product quality while preserving throughput barely
registers, because the kilograms still flow. Several of the disruptions in the
library do exactly that, and a mass-basis metric would have scored the system as
performing well while the plant produced material it could not sell.

The comparative quantity throughout is the paired difference on identical
disruption realizations under common random numbers. Pairing matters more than it
might appear: scenario-to-scenario variance in this system is roughly an order of
magnitude larger than the treatment effect, so an unpaired design would need
something like a hundred times the sample to reach the same interval width. Every
confidence interval reported below is a paired interval, and the campaign is
2,000 scenarios rather than the 200 an unpaired design would have made affordable.

### 3.1 Why this system is a useful test case

Three properties make it a demanding demonstration rather than a convenient one.

It has a genuine treatment. Topology reconfiguration is not a tuning parameter; the
plant is physically rewired, the model is recompiled, and the transient is
integrated. There is a real thing to evaluate, and a real risk that the evaluation
flatters it.

It has a rich comparator space. The static twin can be given a passive policy, a
best-of-two schedule, a best-of-four onset-aware schedule with oracle onset, or a
continuous draw policy, and each of those choices changes the measured effect. That
is what made the comparator-symmetry failure available to be found.

And it has an honest negative already in it. The graph-attention screen does not
generalize to unseen reconfigurations, which we report in Section 5. A system whose
every component worked would have been a weaker vehicle for protocols whose purpose
is to detect when something does not.

## 4. Six protocols

### 4.1 Enforce comparator symmetry

**The failure mode.** Hardening an evaluation usually means strengthening the
baseline. The instinct is correct and incomplete. If a non-treatment improvement
is granted to the baseline and withheld from the treated arm, the comparison
measures the difference in that improvement rather than the effect of the
treatment.

**What we measured** (Figure 1). Our static comparator was strengthened from a
passive policy to an onset-scheduled policy with oracle knowledge of disruption
onset.
Against that hardened baseline the reactive twin scored 0.117, CI [0.093, 0.142].
The result was a formal positive but weak enough to reject the practical claim.
The reactive arm, however, was still running an inferior continuous inventory
policy with pre-drawn buffers. Granting both arms the same continuous policy, and
leaving the baseline its oracle-onset advantage, gave 0.241, CI [0.215, 0.267] on
the same scenarios.

**Why the intuition fails.** Strengthening a baseline feels conservative because
it can only lower the measured effect, and a lower effect that still clears
significance feels like a safer claim. The reasoning holds only when the
strengthening is confined to the baseline arm. If the improvement is one the
treated arm could also have received, then withholding it means the comparison is

$$\Delta = \underbrace{(\text{treatment effect})}_{\text{what is claimed}} - \underbrace{(\text{value of the withheld improvement})}_{\text{silently subtracted}},$$

and the two terms are not separable from the reported number. In our case the
withheld improvement was a continuous inventory policy worth roughly 0.12 in
resilience units, against a treatment effect of roughly 0.24, so the measured
quantity was approximately half the effect and could plausibly have been near zero
had the policy been slightly better.

**The protocol.** Enumerate every improvement granted to either arm and verify it
is available to both, or that its absence is a property of the treatment rather
than of the experiment. Report the enumeration. An asymmetry that favours the
baseline is not conservative; it is a measurement of the wrong quantity, and it
cannot be corrected after the fact because the two terms above are confounded in a
single number.

**What it costs.** Nothing but attention. The enumeration is a paragraph, and in
our case rerunning the corrected comparison used the scenarios already generated.

### 4.2 Benchmark the loop against its own oracle

**The failure mode.** Recurrent architectures rest on the premise that
re-deciding beats deciding once. The premise is plausible enough that it is easy
to leave untested, and it is not free: a loop costs implementation complexity,
compute, and every failure mode that comes with running an optimizer in the
control path.

**The diagnostic.** Run the system's own action set once, at onset, with perfect
foresight of the disruption. That one-shot oracle is an upper bound on any
single-decision policy. If the recurrent loop cannot beat it, recurrence is
contributing nothing and the architecture should be collapsed.

**How to build it.** The oracle is cheaper than it sounds, because it does not
require solving anything hard. Take the system's own action set, reveal the entire
disruption realization, and choose the single best action at onset by enumeration
over that action set. No learning, no optimization under uncertainty, no
implementation of a rival method. In our case the whole arm was a loop over seven
options on scenarios already generated.

**What we measured.** The recurrent loop scored 0.190 against the one-shot
oracle's 0.187. Recurrence wins, but by 0.003. That thin margin is itself the
finding: imperfect information applied repeatedly slightly exceeded perfect
information applied once, and a system with a marginally different option set
could easily fall on the other side. Reporting the margin, rather than the
existence of a gain, tells a reader how much of the architecture is load-bearing.

**What a failure would mean.** Had the loop lost to its own oracle, the correct
response would not have been to discard the system. It would have been to
implement the one-shot version, which is simpler, cheaper to certify, and easier
to explain to an operator. That is the protocol's practical value: it distinguishes
an architecture that earns its complexity from one that has merely accumulated it,
and the second case is a design improvement rather than a defeat.

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

**What to commit, concretely.** A version-controlled file, hashed before the
campaign runs, stating: the endpoints and their acceptance thresholds; the
statistical tests; the exclusion rules; and, most usefully, the shape each result
is expected to take. The last item is what caught our error. Committing "resilience
gain will rise then fall with severity" cost one sentence and detected an
unphysical market assumption that a post-hoc analysis would have described as a
monotone trend and moved past. The commit hash is the evidence, and it costs
nothing to produce in a project already under version control.

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

**Why it is a decision error and not a modeling error.** An optimistic
initialization does not merely inflate the reported benefit, which would be
recoverable by discounting the number. It moves the threshold at which the system
switches from recommending nothing to recommending action. A twin that believes
newly activated equipment contributes immediately will advise reconfiguring during
disruptions that end before the equipment would in fact have become useful, and the
operator who follows that advice pays the switching cost and receives none of the
benefit. The error is in the recommendation, not in the estimate of its value, and
no amount of caution applied to the reported number will catch it.

**The protocol.** State the re-initialization contract explicitly and test the
decision's sensitivity to it. Where the contract is uncertain, report the decision
threshold under both an optimistic and a conservative contract, as we do in Section
5; a threshold that moves by a factor of three between them is a result the reader
needs, not a caveat to be buried.

**What it costs.** This is the one protocol here that required real work: an extra
state variable per activated element, and a rerun of the affected experiments. It
also returned the largest single correction, which is not a coincidence, since it
was the only assumption in the study that nobody had previously examined.

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

### 5.1 The economics, and which way the error ran

The system's economic case is the part of a study like this that a reader trusts
least, and correctly so: it multiplies a simulated benefit by prices and event
frequencies that authors typically assume. We treated those assumptions the way
this paper treats everything else, by writing them into a provenance ledger whose
strict gate fails while any figure remains uncited, and then checking them against
public records.

Two of the load-bearing assumptions could be verified. Utility-outage frequency was
modeled at 6 per year; the national regulator's reliability indices for the plant's
region give 9.2 per year for the best-served urban utility over the recent era, and
41 to 50 per year for the rural cooperatives that serve coconut-growing areas.
Market availability after a disruption was modeled at 0.30 of nominal; deriving it
from national production records as the ratio of the first full quarter after a
typhoon landfall to the same quarter a year earlier gives 0.63 in a directly struck
region and 0.88 in a peripherally struck one, with an off-track control region
returning ratios near unity.

Both assumptions were wrong in the same direction. Recomputing the annualized
benefit at the verified values raises it by a factor of 1.3 for urban siting and
4.0 for cooperative siting. **The published economics were conservative, not
optimistic, which is the opposite of what a reader assumes about an author's own
economic estimate.**

Two things follow, and the second matters more than the first. The direction of a
parameter error is reportable information: an author who has checked knows whether
the headline understates or overstates, and a reader who has not checked can only
assume the latter. And the larger figure exposes a fragility that the smaller one
concealed, because the utility-outage share of the total rises from 51% to 90%
across the siting range. A result resting nine tenths on a single parameter is
fragile however well that parameter is sourced. We therefore report the band and
take the urban case as the headline, which is the most conservative of the verified
options, rather than promoting the largest number the evidence permits.

We considered whether parameter-direction checking belongs as a seventh protocol
and decided against it. It was not found by the six protocols catching a failure;
it was found by building a provenance ledger and then doing the work. That is
ordinary diligence rather than a detectable failure mode, and a protocol set is
more useful for being short than for being complete.

Three prices remain unverified, because the national statistics publish whole-nut
farmgate values while the plant's economics turn on copra, the dried kernel at
roughly four times the value density. Every peso figure therefore scales with an
unverified quantity and is reported as indicative. The ratios between siting cases
do not, and are the defensible content.

We report one negative result about the system itself. Graph-attention screening
does not generalize to reconfigurations absent from training: transfer is negative
at every training-diversity level examined, degrades as diversity grows, and never
exceeds a flat gradient-boosted baseline on identical splits. The layered
architecture is what makes this non-blocking, since the screening slot is filled
by the tabular model and system performance does not depend on the graph model.

## 6. Turning the protocols on ourselves

There is an obvious objection to everything above. Protocols proposed by the same
authors who report the results those protocols validated are not independent
evidence; a set of rules that happens to endorse its inventors' conclusions is
worth little. The only answer we can offer is to show the protocols rejecting
something we wanted to be true.

We had a theory. It was elegant, it distinguished our system from a large
adjacent literature, and it was wrong. We report it in full, along with the
experiments that killed it, because the sequence is the strongest evidence in the
paper that these protocols do work when pointed at a claim the authors are
invested in.

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

## 7. An audit of evaluation practice

A demonstration on one system invites the objection that the protocols detect
problems peculiar to that system. To test whether they discriminate more widely,
we scored roughly thirty published studies of prescriptive decision-support
systems for disruption response against the six protocols.

### 7.1 Method and its limits

Studies were drawn from six areas: power distribution restoration and
reconfiguration, prescriptive digital twins in manufacturing and energy, water and
gas network control, supply-chain disruption response, reinforcement learning for
infrastructure operation, and process-systems resilience. Selection favoured recent
and highly cited work that makes an explicit performance claim against a baseline,
which is a deliberate bias: a paper claiming improvement is a paper whose
comparison matters.

Each protocol was scored SATISFIED, VIOLATED, or NOT REPORTED, and the third
category carries most of the weight. Engineering venues impose page limits, relegate
assumptions to appendices, and have no convention requiring authors to state, for
instance, how a newly activated generator is initialized. **A study scored NOT
REPORTED has not been found deficient. It has been found silent on a question the
field does not currently ask.** We regard the distinction as the audit's central
epistemic commitment, and we report the two categories separately everywhere.

Two further limits bear on how much weight the counts carry. Roughly a quarter of
the scores rest on abstracts and partial texts rather than full methods sections,
and are marked provisional. And the corpus is not a random sample of the
literature; it is a purposive sample biased toward performance-claim papers, which
inflates apparent compliance with the first protocol.

### 7.2 What the audit found

The pattern is consistent across domains (Figure 2) and is summarized rather than
tabulated here, with the full per-study scoring released as supplementary
material.

**Comparator symmetry is widely attempted and rarely achieved.** Almost every study
compares against something, and many comparators are strong: tuned inventory
policies, metaheuristics, exact optimization, and in one case operator-designed
heuristics with safety constraints. Symmetry in the stricter sense, in which the
arms differ in exactly one factor, is uncommon. The recurring pattern in
learning-based work is that the proposed method interacts with a high-fidelity
nonlinear simulator while the optimization comparator solves a linearized or
relaxed model, after which both are scored on the nonlinear model. At least one
study states this asymmetry plainly; others do not.

**Recurrence justification is essentially absent.** Among studies proposing closed
loops, rolling horizons, or learned policies that act repeatedly, we found no case
testing whether re-deciding outperforms deciding once. This is the largest gap the
audit found, and it is a striking one: the premise that justifies the architecture
is the premise least often examined.

**Bounding an unbuilt alternative is rare but demonstrably achievable.** Three
studies do it properly, and they are worth naming because they show the protocol is
not a counsel of perfection. Zhang et al. (2022) report a perfect-foresight upper
bound and state the fraction of it their controller attains. Jacob et al. (2024)
benchmark against an exact mixed-integer conic optimum. A physics-informed
reinforcement-learning study compares directly against an explicit oracle. Elsewhere
the alternative is asserted to be inferior rather than bounded.

**Pre-registration does not occur.** We found no instance in the corpus, which we
expected. More interesting is a partial-credit category: several studies report
confidence intervals over multiple seeds, repeat experiments to separate systematic
effects from simulation noise, or report an honest negative about their own method's
degradation under distribution shift. These are the practices pre-registration
would formalize, and their presence suggests the field is closer to the standard
than the absence of the word implies.

**Re-initialization is almost never reported, and where reported is instantaneous.**
Newly activated generators, storage, tie-switches, pumps and microgrids contribute
at full capability in the step they are activated. Several studies state this
explicitly as an assumption; most do not state it at all. No study in the corpus
reports a sensitivity analysis on the choice. Given that varying this assumption
moved a decision threshold by a factor of three in our own system, this is the
protocol we expect to matter most in practice.

**Detection-inside-policy could not be scored, and the reason is the finding.**
Prescriptive resilience studies overwhelmingly assume the disruption is known:
fault location given, onset observed, no detector in the loop. Meanwhile a separate
fault-detection literature measures detection delay and false-alarm rate carefully,
against a delay-minimization objective, decoupled from any downstream decision. The
two halves of the problem are studied by different communities and joined by
neither. That division is precisely what the protocol exists to surface.

### 7.3 A failure mode the rubric did not anticipate

One study returned a result the instrument was not built to catch, and it is worth
reporting because it generalizes. A deep reinforcement-learning controller for pump
scheduling is compared against classical optimizers, which is a strong comparator
choice. But the optimizer's output is also the reward standard the agent is trained
against: the agent is taught to reproduce the baseline's decisions and then scored
against the baseline. A later paper in the same field states this directly, noting
that taking the optimizer's pump speeds as the optimal setting makes the learned
results depend largely on that optimizer.

The reported figure, efficiency above 0.98 relative to the best-performing
baseline, is therefore close to tautological rather than close to optimal. A
student cannot substantially outscore the examiner who wrote the answer key. The
contribution of the work is real and lies elsewhere, in a speedup of roughly two
times with a controller that runs from measurements alone, but the accuracy
comparison is not independent evidence.

We flag this because it is easy to miss. The baseline is genuinely strong, the
reporting is otherwise careful, and nothing in the comparison looks unfair until
one asks where the training signal came from. The scoring rubric has been extended
to name this case, and it is a reminder that a checklist is only ever a record of
the failures its authors have already encountered.

### 7.4 Single rater, and the instrument for a second

Several of these judgements require reading a methods section for what it does not
say, and reasonable readers will differ. Rather than assert that our scoring was
objective, we measured it. Two raters scored seven papers independently against the
rubric, with the first rater's codes sealed until the second rating was recorded.
The threshold that would invalidate the audit was fixed in advance: a kappa below
roughly 0.4 would mean the rubric was not operational enough to publish, and the
audit would be revised before being reported rather than after.

Pooled Cohen's kappa was 0.818, with a bootstrap interval of [0.68, 0.94] over
papers, and raw agreement of 0.86. Six of forty-two cells disagreed.

The distribution of those six is more informative than the pooled figure. **Five of
the six were disagreements between Satisfied and Partial: both raters saw the same
practice and differed on whether it fully or partly met the protocol. Not one was a
disagreement about whether a practice was a problem.** Agreement was perfect on
re-initialization, kappa 1.000, where the raters never differed on whether the
contract was reported. The detection protocol was degenerate, both raters assigning
Not Applicable to every paper, which is itself the finding that prescriptive
studies assume disruption is known.

The instrument therefore identifies problems reliably and grades degrees of
compliance unreliably, and this bounds what we claim. The counts of Not Reported
and Violated, which is where the audit's conclusions live, are trustworthy. Any
finer ranking of which studies evaluated *best* is not, and we do not offer one.

Adjudication changed three cells between Satisfied and Partial and moved one to Not
Applicable, leaving all four headline findings unchanged. It also exposed four
genuine ambiguities in the rubric rather than reading errors, each now amended: the
boundary for when recurrence is applicable, the requirement that pre-registration
be evidenced rather than inferred from good statistical practice, a rule for
studies whose several comparators differ in symmetry, and a separation between
bounding an unimplemented alternative and computing a performance ceiling. Three of
the six disagreements arose from the second of these, because the protocol's name
invites reading it as a general statistical-rigor score. The full adjudication,
with reasoning per cell, is released with the instrument.

### 7.5 What the audit does and does not establish

It establishes that the failure modes are not peculiar to our system. Four of the
six protocols address questions that the surveyed literature does not routinely
ask, and one addresses a question split across two communities that do not
reference each other.

It does not establish that the answers, had they been reported, would have been
wrong. A study that does not report its re-initialization contract may have modeled
it carefully. The audit measures what evaluations report, and reporting is a
convention. What we can say is that a reader of these studies cannot currently tell,
and that in the one case we examined closely, our own, the answer mattered by
factors of two and three.

## 8. Discussion

**On what generalizes.** Nothing in these six protocols is about coconuts, about
digital twins, or even about resilience. Each addresses a failure that becomes
available the moment a prescriptive system is judged against a baseline its own
evaluator designed, and that arrangement is close to universal in the field. We expect them to transfer to prescriptive systems in
power dispatch, water network operation, and supply-chain control, Section 7 reports a first pass at whether published
evaluations in those domains satisfy the protocols; the short answer is that four
of the six address questions the literature does not routinely ask.

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

### 8.1 Using these protocols

A reader persuaded by the argument still has to act on it, so we state what
adoption costs and in what order we would do it.

Four of the six are essentially free and can be applied to an evaluation already
designed. The symmetry enumeration is a paragraph. The oracle arm is a loop over
the system's own action set on scenarios already generated. Pre-registration is a
hashed file. Charging the detector's real delays to the loop is a choice about
which arm to report. None of these requires new modeling, and together they caught
the effect-size error, the architecture question, and the detection sign error in
our study.

Bounding an unbuilt alternative costs more thought but rarely more code: the
envelope we used is the pointwise maximum over two policies already implemented.
The re-initialization protocol is the expensive one, requiring a state variable per
activated element and a rerun, and it is also the one that produced the largest
correction. If a reader adopts only one protocol, we would suggest symmetry, on the
grounds that it is free and it was the error that would have changed our
conclusion. If a reader adopts two, the second should be re-initialization, because
it is the error that would have changed our recommendation.

We also note what these protocols do not do. They do not check that a model is
right, that a metric is meaningful, or that a system is worth building. They check
that a comparison measures the decision the system actually makes. That is a narrow
service, and the failures it catches are correspondingly specific.

## 9. Limitations

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

### 9.1 The n equals one problem

The most serious limitation is structural and no amount of care removes it. Six
protocols are demonstrated on one system, one plant archetype, one disruption
library. We have shown that each detected a real failure in this study. We have
not shown that any of them detects failures in general, still less that the set is
complete.

Three considerations bear on how far the results travel, and we state them so a
reader can weigh them rather than take our word.

The failure modes are mechanism-driven rather than incidental. Comparator
asymmetry misleads because the comparison then measures the difference in the
withheld improvement, which is an argument about experimental design and not about
coconut processing. The re-initialization result follows from a newly activated
unit taking time to become useful, which is true of physical equipment generally.
Detection latency pays under a hoarding policy because undetected time is
accumulation time, which is a property of the policy rather than of the plant.
Arguments of this shape suggest transfer, but they do not demonstrate it.

Against that, the magnitudes are certainly system-specific. Whether asymmetry
costs a factor of two, as it did here, or a few percent elsewhere, is not
predictable from our data. A reader should take the existence of each failure mode
as demonstrated and the size of each as one observation.

Section 7 reports a first attempt at the decisive test: an audit of published
prescriptive-system evaluations scored against the six protocols. That audit is
preliminary, and its limitations are stated there, but it moves the evidence
beyond a single system.

## 10. Conclusions

Prescriptive systems are judged by comparison, and the comparison belongs to the
person doing the judging. Within a single study, ordinary and defensible choices
about that comparison gave us an effect estimate wrong by a factor of two, a
decision threshold wrong by a factor of three, and a detection result carrying the
wrong sign. None of the three announced itself. Each was found only because
something in the protocol forced the question.

That is the argument for the six protocols assembled here, and it is worth being
clear about how modest a claim it is. We have not proved them necessary, we have
not proved them sufficient, and we have demonstrated them on one system. What we
can say is that they were enough to catch three errors we had already made, and
enough to reject four explanations we would have preferred to keep.

The resilience result that survived, a 0.244 improvement in the 72-hour resilience
integral for runtime topology reconfiguration under typhoon-calibrated disruption,
is the least interesting sentence in this paper. It is also the one we trust,
which is the entire point: it is not a stronger number than we started with, but
it is a number that was given every reasonable opportunity to be smaller.

---
*Figures (2): Figure 1, comparator hardening across five evaluation designs, in
which a stronger but asymmetric baseline halves the measured effect (repo F7).
Figure 2, consensus audit scores by protocol, with the reliability caveat of
Section 7.4 stated in the caption (repo F10).*

## Data and code availability

The complete simulator, disruption library, analysis pipeline, and every
experiment reported here, including the falsified ones, are publicly available at
https://github.com/beebzy-droid/rdt-thesis3 behind a one-command reproducibility
harness with a determinism-verified rebuild path.
