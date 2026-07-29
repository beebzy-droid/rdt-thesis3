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
