# Transition Dynamics as the Binding Constraint on Reactive Reconfiguration

*Theoretical core, v1, 2026-07-13. Four propositions with proofs, an empirical
test against the simulation campaign, and the regional design criterion that
places the Philippine setting inside the contribution rather than beside it.*

## 0. Why a theory is needed

Online topology reconfiguration is a solved problem in one engineering domain and
an open one in another, and the difference is a single physical quantity. Electric
distribution networks have reconfigured themselves under fault for decades: a
switch opens, a switch closes, and the network re-solves in milliseconds. The
literature on distribution network reconfiguration is correspondingly mature,
including recent work that screens candidate topologies with graph attention and
selects them by mixed-integer programming.

A process plant cannot do this. Rerouting material through a different train
requires draining lines, re-establishing thermal and compositional steady state,
and moving inventory through vessels whose residence times are measured in hours.
In the reference plant studied here the dryer chain alone has a design residence
of 30 hours. A reconfiguration is therefore not an instantaneous switch but a
*transient of the same order as the disruption it responds to*, and during that
transient the plant produces less than it would have produced by doing nothing.

This single fact changes the decision problem from "which topology is best" to
"is this disruption long enough to be worth the transition." Everything below
formalizes that question, and Section 4 shows the answer is a plant property that
meets a climate property, which is where the Philippine setting enters as a
quantitative criterion rather than a case study.

## 1. Setup

Consider a horizon $[0,T]$ with a disruption arriving at $t=0$ and persisting for
a duration $D$. Write $v(t) = P(t)/P_0$ for the instantaneous production value
rate normalized to its pre-disruption level, so that the resilience integral of
Section 3.3 of the manuscript is

$$R(T) \;=\; \frac{1}{T}\int_0^T v(t)\,dt .$$

Under the static policy the plant is degraded to a rate $v_d < 1$ for the duration
of the disruption and recovers thereafter. Under reconfiguration option
$k \in \mathcal{K}$, initiated at onset, the trajectory passes through three
regimes:

| Interval | Rate | Interpretation |
|---|---|---|
| $[0,\ \tau_k)$ | $v_{\tau,k}$ | forward transition, typically $v_{\tau,k} \le v_d$ |
| $[\tau_k,\ D)$ | $v_{r,k}$ | reconfigured operation, $v_{r,k} > v_d$ for a rescue option |
| $[D,\ D+\tau_k')$ | $v_{\tau,k}'$ | return transition to the nominal topology |

with nominal operation resuming on $[D+\tau_k',\,T]$. Define the two quantities
that will carry the whole argument:

$$\gamma_k \;=\; v_{r,k} - v_d \qquad\text{(rescue margin)}$$

$$c_k \;=\; \underbrace{(v_d - v_{\tau,k})\,\tau_k}_{\text{forward switching cost}} \;+\; \underbrace{(1 - v_{\tau,k}')\,\tau_k'}_{\text{return switching cost}} \qquad\text{(switching cost)}$$

Both are integrated value quantities: $\gamma_k$ is a rate, $c_k$ is a rate times
a time. Note that $c_k \ge 0$ whenever the transition depresses output, which is
the physically ordinary case.

## 2. Proposition 1: the breakeven duration

**Proposition 1.** *For $\tau_k \le D$ and $D + \tau_k' \le T$, the resilience gain
from reconfiguration is linear in the disruption duration,*

$$\Delta R_k(D) \;=\; \frac{\gamma_k}{T}\,\bigl(D - D_k^{*}\bigr), \qquad
D_k^{*} \;=\; \tau_k + \frac{c_k}{\gamma_k},$$

*so reconfiguration improves resilience if and only if $D > D_k^{*}$.*

**Proof.** Integrating the static trajectory gives
$\int_0^T v_{\text{static}} = v_d D + (T-D)$. Integrating the reconfigured
trajectory over the three regimes and the nominal tail gives

$$\int_0^T v_{\text{recon}} = v_{\tau,k}\tau_k + v_{r,k}(D-\tau_k) + v_{\tau,k}'\tau_k' + \bigl(T - D - \tau_k'\bigr).$$

Subtracting, and splitting $v_d D = v_d\tau_k + v_d(D-\tau_k)$,

$$T\,\Delta R_k(D) = (v_{\tau,k}-v_d)\tau_k + (v_{r,k}-v_d)(D-\tau_k) - (1-v_{\tau,k}')\tau_k'
= \gamma_k (D - \tau_k) - c_k .$$

Setting the right side to zero and solving for $D$ yields $D_k^{*}$, and
substituting back gives the stated linear form. $\blacksquare$

Two immediate readings. First, $D_k^{*}$ decomposes into a *physical* term
$\tau_k$, the time the plant needs to complete the change, and an *economic* term
$c_k/\gamma_k$, the switching cost amortized against the rescue margin. Second,
an option with a large rescue margin tolerates a large switching cost, which is
why high-value reroutes can be worth a long changeover and marginal ones cannot.

**Corollary 1.1 (saturation).** *For $D \ge T$ the disruption outlasts the
evaluation window and*
$$T\,\Delta R_k = (v_{\tau,k}-v_d)\tau_k + (v_{r,k}-v_d)(T-\tau_k),$$
*which is independent of $D$.* The gain therefore rises linearly in duration up to
the horizon and is flat beyond it. This piecewise form is a falsifiable prediction
and is tested in Section 5.

## 3. Corollary 2: why the power-systems literature never asks this

**Corollary 2.** *As $\tau_k, \tau_k' \to 0$ with bounded rates, $c_k \to 0$ and
$D_k^{*} \to 0$, so $\Delta R_k(D) > 0$ for every $D > 0$.*

When switching is instantaneous the breakeven duration vanishes and every rescue
option is unconditionally beneficial. The decision collapses to "select the best
available topology," which is precisely the problem distribution network
reconfiguration solves. The conditional structure that dominates process
reconfiguration is not a modeling choice; it is a consequence of
$\tau_k$ being comparable to $D$.

This is the formal statement of the domain boundary. Methods transported from
network reconfiguration to process plants inherit an assumption, $\tau \approx 0$,
that process physics violates by two to three orders of magnitude. The
contribution of a reactive digital twin for process networks is therefore not the
reconfiguration machinery, which exists elsewhere, but the machinery required
once $\tau$ is no longer negligible: a transient model that decides whether the
change is reachable in time to matter.

## 4. Propositions 3 and 4: deciding under duration uncertainty

At onset $D$ is not observed. Let $D \sim P$ be the belief implied by the detector
and by regional climatology.

**Proposition 3 (one-shot policy and the value of duration information).**
*Under a single decision at onset, reconfiguring with option $k$ has expected gain
$\mathbb{E}[\Delta R_k] = (\gamma_k/T)(\mathbb{E}[D] - D_k^{*})$, so the option is
worth taking if and only if $\mathbb{E}[D] > D_k^{*}$. The expected value of
perfect duration information is*

$$\mathrm{EVPI}_k \;=\; \frac{\gamma_k}{T}\Bigl\{\mathbb{E}\bigl[(D - D_k^{*})^{+}\bigr] - \bigl(\mathbb{E}[D] - D_k^{*}\bigr)^{+}\Bigr\} \;\ge\; 0,$$

*with strict inequality if and only if $\;0 < \Pr(D > D_k^{*}) < 1$.*

**Proof.** Linearity of $\Delta R_k$ in $D$ gives the first claim directly. With
perfect information the decision maker reconfigures exactly when $D > D_k^{*}$,
earning $(\gamma_k/T)\mathbb{E}[(D-D_k^{*})^{+}]$; without it the best fixed action
earns $(\gamma_k/T)(\mathbb{E}[D]-D_k^{*})^{+}$. Non-negativity follows from
Jensen's inequality applied to the convex map $x \mapsto x^{+}$, and equality holds
exactly when $x \mapsto x^{+}$ is affine on the support of $D - D_k^{*}$, that is
when the support lies entirely on one side of zero. $\blacksquare$

The economic content is worth stating plainly: **duration information has value
precisely when the disruption distribution straddles the breakeven.** If every
disruption is short relative to $D_k^{*}$, never reconfigure and measure nothing;
if every disruption is long, always reconfigure and measure nothing. The
measurement problem exists only in the overlap. This predicts that the empirical
value of duration information should concentrate in the option-category pairs
whose duration distributions straddle their breakevens, which is a testable claim
about *where* the screening gap of Section 4.2 of the manuscript comes from.

**Proposition 4 (recurrence versus one-shot optimality).** *Let $k^{*}(s)$ denote
the option maximizing $\gamma_k(s - D_k^{*})$ for remaining duration $s$, and let
$\sigma$ denote the cumulative switching cost of an intermediate change. A
recurrent policy that re-decides as the disruption reveals itself attains value at
least*
$$\max_k \Delta R_k(D) \;+\; \frac{1}{T}\Bigl[\text{sequencing gain}\Bigr] \;-\; \frac{\sigma}{T},$$
*and strictly exceeds the one-shot perfect-foresight optimum whenever $k^{*}(\cdot)$
is non-constant on the realized remaining-duration path and the sequencing gain
exceeds $\sigma$.*

**Proof sketch.** A one-shot policy selects a single $k$ and is bounded by
$\max_k \Delta R_k(D)$ even with perfect foresight. A recurrent policy realizes the
upper envelope of the per-option gain rates over the remaining-duration path, less
the switching cost incurred at each change. The envelope pointwise dominates any
single member; the inequality is strict when the argmax changes, and net of
$\sigma$ when the envelope gain exceeds the switching cost. $\blacksquare$

This is the formal explanation for the empirical inversion in which the recurrent
loop scored 0.190 against the one-shot oracle's 0.187. The margin is thin because
the two terms in Proposition 4 are close: sequencing gain and intermediate
switching cost nearly cancel in this plant. The proposition also yields a design
rule. A closed loop earns its complexity only when the option ranking is
state-dependent, and if it is not, the architecture should be simplified to a
single decision.

## 5. Empirical test against the campaign

Proposition 1 predicts that per-option gain is linear in duration below the
horizon with a zero at $D_k^{*}$; Corollary 1.1 predicts it is flat above the
horizon. Both are falsifiable. Fitting the 1,120 committed option-scenario rows
(`scripts/breakeven_analysis.py`, 2,000 bootstrap resamples, $T = 72$ h) gives:

| Option | $\hat{D}^{*}$ (h) | 95% CI | slope below $T$ | slope above $T$ | $\Pr(D > \hat{D}^{*})$ |
|---|---|---|---|---|---|
| copra_buy | $-33.0$ | $[-219,\,-1.0]$ | $+1.8\times10^{-3}$ | $-5.7\times10^{-6}$ | 1.00 |
| solar_train | $-19.5$ | $[-69.6,\,-2.4]$ | $+2.6\times10^{-3}$ | $+4.1\times10^{-12}$ | 1.00 |
| wet_route | $-2.2$ | $[-23.4,\,+7.6]$ | $+3.8\times10^{-3}$ | $0$ | 1.00 |
| **nut_sale** | $\mathbf{+33.5}$ | $\mathbf{[21.8,\,69.3]}$ | $+8.7\times10^{-4}$ | $0$ | 0.78 |
| **crude_bypass** | $\mathbf{+51.0}$ | $\mathbf{[31.4,\,366.8]}$ | $+9.5\times10^{-4}$ | $0$ | 0.66 |
| copra_sale | $+1510$ | $[-2364,\,2732]$ | $+4.9\times10^{-5}$ | $0$ | 0.00 |
| shell_boiler | $-5.1\times10^{4}$ | wide | $+2.6\times10^{-7}$ | $+1.2\times10^{-7}$ | 1.00 |

**The saturation prediction survives cleanly.** The median ratio of the
above-horizon slope to the below-horizon slope is $0.000$: gain rises with
duration up to the evaluation window and is exactly flat beyond it. A ratio near
unity would have falsified the finite-horizon rescue-time model of Section 1, and
this is the sharpest available test of it.

**The partition is the theory's signature.** Four options are unconditional
($\hat{D}^{*} \le 0$, benefit at any duration) and three are conditional. The two
identified conditional options are `nut_sale` at 33.5 h and `crude_bypass` at
51.0 h, both with bootstrap intervals excluding zero. The crude bypass surrenders
the refined-product premium and requires re-establishing a separate route, so it
carries a large $c_k$ against a modest $\gamma_k$; its breakeven lands near twice
the 30 h dryer residence, and its mean gain over sampled durations is negative,
which is exactly the behavior Proposition 1 assigns to an option whose breakeven
sits above the median disruption. Under Corollary 2 an instantaneous-switching
domain would place every option in the unconditional partition. The conditional
partition is therefore the empirical signature of non-negligible transition time.

**Sensitivity to the transition timescale.** Because $D^{*} = \tau + c/\gamma$
depends on $\tau$ with unit slope, the theoretical prediction inherits whatever
uncertainty attaches to the dryer residence time. The model uses 30 h as a
mid-range value, but the authoritative Philippine figure, from the PCA Zamboanga
Research Center mechanical dryer, is approximately 24 h, while small-holder
indirect dryers run nearer 36 h. Taking the crude bypass as the test case, a
forward plus return transition predicts $D^{*}$ near $2\tau$, giving 48 h at
$\tau = 24$ h, 60 h at 30 h, and 72 h at 36 h, against an empirical estimate of
51.0 h with a bootstrap interval of [31.4, 366.8]. All three lie inside the
interval, and the authoritative 24 h figure gives the closest agreement, which is
worth reporting because it favors the source we did not use. The parameter is
recorded in the provenance ledger as a range rather than a point value, and no
claim in this paper depends on resolving it.

**An unplanned consistency check.** Two options, `copra_sale` and `shell_boiler`,
return breakeven estimates that are numerically absurd (1,510 h and
$-5\times10^{4}$ h) with intervals spanning zero. This is not noise: both have
near-vanishing rescue margins, with duration slopes two to four orders of
magnitude below the others. Proposition 1 states $D_k^{*} = \tau_k + c_k/\gamma_k$,
so as $\gamma_k \to 0$ the breakeven diverges and ceases to be identifiable. The
options whose breakevens the data cannot pin down are exactly the options the
theory says should be unidentifiable, which is a check the analysis was not
designed to perform.

## 5.1 A falsified prediction, and what it reveals about the model

Proposition 1 makes a second, sharper prediction than the saturation result:
because $D^{*} = \tau + c/\gamma$ depends on $\tau$ with unit slope, sweeping the
dominant transition timescale should move every breakeven one hour per hour.
`scripts/tau_sweep.py` tests this by rebuilding the plant at
$\tau_{\text{dry}} \in \{12, 18, 24, 30, 36, 48\}$ h and re-estimating each
breakeven, over 960 option-scenario labels spanning two disruption categories and
both the control-input and topology-activation option families.

**The prediction fails.** Measured slopes are:

| Option | family | $dD^{*}/d\tau$ | 95% CI |
|---|---|---|---|
| solar_train | topology (adds dryer compartments) | $-0.01$ | $[-0.03,\,-0.01]$ |
| nut_sale | topology | $0.00$ | $[0.00,\,0.00]$ |
| crude_bypass | control input | $+0.09$ | $[0.05,\,0.16]$ |
| wet_route | control input | $0.00$ | $[0.00,\,0.00]$ |
| copra_buy | control input | $-0.03$ | $[-0.05,\,0.00]$ |

against a predicted $1.00$. The breakevens are essentially independent of the
dryer residence time, and this holds even for `solar_train`, whose reconfiguration
activates five additional dryer compartments and whose transition should therefore
be residence-gated.

**The cause is the re-initialization contract, not the theory.** When a topology
change activates new units, the state remap of `warm_start_map` assigns new
states from a defaults dictionary, and the topology label generator supplies
inlet moisture for the new dryer compartments. Newly activated vessels are
therefore born already filled with material at inlet condition, and begin
contributing output as soon as flow reaches them. The effective transition time is
set by how quickly flow redistributes, on the order of hours, and not by the
residence time of the vessels being brought online, on the order of a day. With
$\tau_{\text{effective}}$ decoupled from $\tau_{\text{dry}}$, the sweep cannot
move the quantity it is trying to move.

**The consequence is uncomfortable and must be stated plainly.** In its present
form the simulator represents reconfiguration as nearly instantaneous, which is
the regime Corollary 2 attributes to power distribution networks. The economic
component of the breakeven, $c/\gamma$, is real and is what the estimates of
Section 5 measure: `crude_bypass` remains net harmful on short disruptions
because it surrenders the refined-product premium, and that is an economic
threshold, not a transition-time one. But the transition-time component of the
theory, which is the part that distinguishes this work from the network
reconfiguration literature, **is not demonstrated by the current model.**

Two things follow. First, any claim that transition dynamics bind must wait on a
cold-start re-initialization contract in which newly activated units begin empty
or at ambient condition and must fill and reach a steady profile before
contributing, making the transition genuinely residence-gated. That is a
well-defined modeling change and it is the next experiment, not a limitation to be
argued around. Second, the requirement itself is a finding worth reporting: a
digital twin that hot-starts newly activated units will systematically
underestimate the cost of reconfiguring, and will therefore recommend
reconfigurations that a real plant would not survive. Model fidelity in the
re-initialization contract is not a numerical detail; it determines whether the
decision the twin recommends is the right one.

## 5.2 The cold-start contract, and a scope limit on Proposition 1

Section 5.1 traced the failed unit-slope test to a re-initialization contract that
hot-starts newly activated units. `PlantParams(cold_start=True)` adds the missing
physics: a per-train commissioning availability $a \in [0,1]$ with
$\dot{a} = (1-a)/\tau_{\text{com}}$, $\tau_{\text{com}} = \tau_{\text{dry}}$,
ramping the train's intake as it fills and establishes a moisture profile. The
state initializes at zero on activation, so commissioning is genuinely
residence-gated. The flag is opt-in and the default reproduces all previously
reported results exactly.

Re-running the sweep under both contracts, for the solar-train option whose
activation adds dryer capacity:

| Contract | $D^{*}$ at $\tau = 12$ | at $\tau = 24$ | at $\tau = 36$ | at $\tau = 48$ | $dD^{*}/d\tau$ | 95% CI |
|---|---|---|---|---|---|---|
| hot start | 4.3 h | 3.9 h | 3.8 h | 3.7 h | $-0.01$ | $[-0.03,\,-0.01]$ |
| **cold start** | **12.2 h** | **14.2 h** | **15.1 h** | **15.6 h** | **$+0.09$** | **$[0.05,\,0.14]$** |

Two results, one of which is a correction to this paper's own theory.

**The re-initialization contract changes the decision.** Cold starting raises the
breakeven by a factor of three to four and reverses the sign of its dependence on
residence time. A twin that hot-starts newly activated units will recommend
reconfigurations at disruption durations where a real plant would lose money, and
the error is not marginal. We regard this as the most transferable practical
finding in the paper: re-initialization fidelity is a first-order determinant of
whether a prescriptive twin's recommendation is correct, and it is routinely
treated as a numerical implementation detail.

**Proposition 1 applies to substitutive options, not additive ones.** The slope
moves in the right direction but reaches only 0.09, far from the predicted unity,
and the reason is a scope condition the derivation of Section 1 left implicit. That
derivation assumed $v_{\tau,k} \le v_d$: during the transition the plant produces
*less than it would have by doing nothing*, because the reconfiguration sacrifices
the currently operating path. The solar train violates this. It adds capacity in
parallel while the primary train keeps running, so commissioning delays the gain
but never depresses output below the do-nothing baseline. With $v_{\tau} \approx v_d$
the switching cost $c_k \approx 0$, the term $c_k/\gamma_k$ vanishes, and the
breakeven is governed by the shape of the commissioning ramp rather than by
$\tau + c/\gamma$.

The proposition should therefore be read with an explicit taxonomy:

- **Substitutive options** reroute material away from an operating path and
  sacrifice its output during the change. These have $c_k > 0$ and are the
  options Proposition 1 describes. The crude bypass is the clearest instance in
  this plant, surrendering the refined-product premium, and it carries the largest
  measured breakeven at 51 to 70 h.
- **Additive options** bring parallel capacity online without disturbing the
  operating path. These have $c_k \approx 0$, a breakeven set by commissioning
  delay alone, and only weak dependence on $\tau$.

This is a genuine limitation on the result as originally stated, and it defines
the next experiment precisely: extend the cold-start contract to a substitutive
option and test the unit slope where the theory predicts it should hold. Until
that is done, the transition-time mechanism is demonstrated to *matter*, through
the threefold change in breakeven between contracts, but the specific
$\tau + c/\gamma$ decomposition remains confirmed only in its saturation
prediction and its identifiability behaviour, not in its slope.

## 5.3 Three failed attempts, and a revision to the mechanism

A third experiment extended the commissioning contract to the crude bypass, a
substitutive option that surrenders the refining premium and therefore looked like
the case Proposition 1 was written for. Sweeping its own commissioning constant
$\tau_{\text{com}} \in \{2,\dots,48\}$ h gives $D^{*} = 69.3 \to 68.7$ h,
slope $-0.01$, CI $[-0.02,\,0.00]$. A third null.

The three attempts and their diagnoses:

| Experiment | Result | Why |
|---|---|---|
| $\tau_{\text{dry}}$ swept against control-input options | slope $\approx 0$ | those options bypass the dryer; wrong $\tau$ |
| $\tau_{\text{dry}}$ swept against the solar train | slope $-0.01$ | additive option: parallel capacity, $v_\tau \approx v_d$, so $c \approx 0$ |
| $\tau_{\text{com}}$ swept against the crude bypass | slope $-0.01$ | the gate delays the option's *effect*, it does not open a value *gap*; again $c \approx 0$ |

The pattern is not a sequence of implementation accidents. It is a structural
property of the plant: **no option in this superstructure satisfies
$v_{\tau,k} \le v_d$.** Every modeled reconfiguration either adds parallel
capacity or monetizes a stream that would otherwise back up. None of them requires
breaking a working path before its replacement is available, which is the only
circumstance under which a transition depresses output below the do-nothing
baseline. With $c_k \approx 0$ throughout, the term $c_k/\gamma_k$ vanishes and
$D^{*} \approx \tau_k$, yet the measured breakevens are far larger than any
transition timescale in the plant. The decomposition therefore does not explain
them.

**What generates the observed conditionality is a standing opportunity cost, not
a transition.** The crude bypass sacrifices the refined-product premium
continuously for as long as it is active, and that sacrifice is repaid only if the
disruption lasts long enough for the constraint it relieves, crude tank fill and
the consequent press throttle, to actually bind. Writing $\lambda_k$ for the rate
of standing value sacrificed while option $k$ is active and $\rho_k$ for the rate
of loss it averts once the relieved constraint binds at time $D_k^{\text{bind}}$,
the breakeven satisfies

$$\rho_k\bigl(D - D_k^{\text{bind}}\bigr) = \lambda_k D
\quad\Longrightarrow\quad
D_k^{*} = \frac{\rho_k D_k^{\text{bind}}}{\rho_k - \lambda_k},$$

which is an economic ratio governed by when a constraint binds, not by how long a
transition takes. This form reproduces the qualitative facts the data show: a
breakeven well above any physical timescale, options that are net harmful on short
disruptions, and insensitivity to residence times.

**The consequence for the contribution must be stated without hedging.** The claim
that transition dynamics are the binding constraint on reactive reconfiguration,
and the resulting boundary against the power-systems literature via
$\tau \to 0$, are **not supported by this model.** The conditional structure is
real and the breakevens are real, but their mechanism is the timing of constraint
activation under a standing opportunity cost, and an instantaneous-switching
network faces a recognizable version of that same problem. Corollary 2 remains
valid as mathematics and as a statement about what *would* distinguish the
domains; it is not currently a statement about what distinguishes this plant.

What survives unchanged, and is independently useful: the saturation prediction of
Corollary 1.1, confirmed at a slope ratio of 0.000; the identifiability behaviour
of Section 5, in which options with vanishing rescue margin have unidentifiable
breakevens exactly as the algebra requires; and the re-initialization finding of
Section 5.2, that hot-starting newly activated units understates the breakeven
three- to fourfold. That last result is genuinely about transition fidelity, and
it stands on its own without requiring the breakeven to be transition-governed.

One temptation must be named and refused. It would be straightforward to add
break-before-make physics, throttling the refining path on commitment while the
off-take commissions, and thereby manufacture the value gap that
$v_\tau \le v_d$ requires. That would make the slope test pass. It would also be
fitting the plant to the theory rather than the theory to the plant, and the
resulting number would mean nothing. Such a mechanism should be added only if a
specific reconfiguration in a real facility genuinely requires breaking its
current route before the replacement is available, in which case it is physics and
belongs in the model on its own merits.

## 6. The regional design criterion

Proposition 3 makes the value of a reconfiguration capability an explicit product
of two independent quantities:

$$\mathbb{E}\bigl[\Delta R_k\bigr] \;\propto\; \underbrace{\gamma_k}_{\text{plant economics}} \times \underbrace{\mathbb{E}\bigl[(D - D_k^{*})^{+}\bigr]}_{\text{climate} \,\times\, \text{plant physics}} .$$

$D_k^{*}$ is a property of the *plant*: residence times, switching costs, product
margins. The distribution of $D$ is a property of the *region*: what disrupts
supply and utilities there, and for how long. A reactive digital twin is worth
building where these overlap, and worth nothing where they do not.

**Criterion.** *Reconfiguration capability for option $k$ has positive expected
annual value $f\,\gamma_k\,\mathbb{E}[(D-D_k^{*})^{+}]\,V_0/T$ at disruption
frequency $f$, and is worthless when $\Pr(D > D_k^{*}) = 0$.*

This is where the Philippine setting becomes load-bearing rather than incidental.
The archipelago sits in the most active tropical cyclone basin on the planet, and
the disruptions that matter for agro-processing there are long: feedstock supply
interruptions measured in weeks after a landfall, utility outages measured in days
in the affected provinces, and multi-season production deficits where standing
palms are destroyed. Against plant breakevens on the order of one to three days,
$\Pr(D > D^{*})$ is large, and by the criterion above the capability pays.

The same plant in a region whose disruptions are short and frequent rather than
long and severe would show $\Pr(D > D^{*}) \approx 0$ and should not be built. The
criterion is thus a transferable design test, and the Philippine case is the
instance where it evaluates most strongly positive. Quantifying
$\Pr(D > D^{*})$ from PAGASA cyclone climatology, ERC distribution-reliability
indices, and PCA post-typhoon production records is the verification work that
converts this section from a qualitative argument into a regional design number,
and is the subject of the companion paper.

## 7. What this changes about the contribution

The architecture is no longer the claim. The claim is that process-plant
reconfiguration is governed by a breakeven between transition time and disruption
duration; that this breakeven is absent by construction from the network-
reconfiguration literature the methods are borrowed from; that it explains, in
closed form, why duration information has the measured value it does and why a
recurrent loop can beat a one-shot oracle; and that it yields a regional design
criterion under which the Philippine typhoon environment is not a case study but
the condition that makes the capability worth having.
