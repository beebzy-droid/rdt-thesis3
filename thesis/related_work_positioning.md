# Related Work: Reconfiguration Across Domains, and Where Process Plants Depart

*Positioning section, v1, 2026-07-13. Written in response to a desk rejection on
novelty grounds. Its purpose is to credit the literatures that already solve
online topology reconfiguration, and then to state precisely, and formally, the
regime they do not address. Intended as Section 2 of the reframed manuscript.*

## 2.1 Topology reconfiguration is a solved problem in power distribution

Any claim to reconfigure a network online must begin by acknowledging that power
engineers have been doing it since the late 1980s. Distribution network
reconfiguration (DNR) opens and closes sectionalizing and tie switches to change
the operating topology of a radial feeder network, and the formulation of Baran
and Wu (1989) established the problem in the form still used today. The field is
mature: it is canonically a mixed-integer nonlinear program, routinely relaxed to
mixed-integer conic or linear form, and comprehensive surveys now classify dozens
of solution families (Mahdavi et al., 2021). Transmission-side topology control
has a parallel lineage beginning with optimal transmission switching (Fisher et
al., 2008). Reconfiguration under fault, rather than for loss minimization, has
its own substantial literature under the headings of service restoration and
self-healing networks.

Learning-based methods arrived in this field before they arrived in ours. Deep
reinforcement learning has been applied to distribution reconfiguration for
several years, and graph neural networks are now standard for encoding the
network state. Most directly relevant to the present work, Guo et al. (2025)
combine a graph attention network with deep deterministic policy gradient to
solve active distribution network dynamic reconfiguration online, encoding the
grid as a graph with time-varying node and edge interactions. A reader who knows
this paper and encounters a proposal to screen topology changes with graph
attention will reasonably ask what is left to contribute. The answer is not a
better architecture. It is a different problem, and the difference is physical.

## 2.2 What "dynamic" means in that literature, and what it cannot represent

Three properties of the DNR formulation, all visible in Guo et al. (2025) and
general across the field, define its boundary.

**Switching is instantaneous.** A breaker operates in milliseconds against load
dynamics of minutes to hours, so the transition between topologies has no
representation in the model. The network is in configuration A, then it is in
configuration B, and the power flow equations are re-solved.

**Switching cost is therefore a count, not a duration.** Where the cost of
changing topology appears at all, it appears as a limit on the *number* of
operations, motivated by breaker wear and system stability. Guo et al. (2025)
constrain the summed absolute change in switch state per period and per breaker
for exactly this reason. There is no term with units of time, and none is needed.

**"Dynamic" means multi-period, not transient.** In DNR, dynamic reconfiguration
means re-solving the topology across a load and generation time series, typically
in hourly steps over a day. Guo et al. (2025) set their horizon to 24 hours in
one-hour increments. This is a sequence of steady-state snapshots linked by a
switching-count constraint, not an integration of the plant through the change.

These are not oversights. They are correct modeling choices for a domain in which
the transition genuinely is instantaneous relative to everything else. The
consequence, however, is that the DNR formulation cannot express the question a
process plant must answer, because in that formulation the question does not
arise.

## 2.3 The boundary, stated formally

Section 3 of this paper derives the gain from reconfiguring with option $k$ as

$$\Delta R_k(D) = \frac{\gamma_k}{T}\bigl(D - D_k^{*}\bigr), \qquad
D_k^{*} = \tau_k + \frac{c_k}{\gamma_k},$$

where $D$ is the disruption duration, $\tau_k$ the transition time, $\gamma_k$ the
rescue margin, and $c_k$ the integrated production loss incurred during the
transition. The breakeven $D_k^{*}$ is the disruption duration below which
reconfiguring is worse than doing nothing.

As $\tau_k \to 0$ the switching cost $c_k \to 0$ and $D_k^{*} \to 0$, so every
rescue option becomes unconditionally beneficial and the decision collapses to
selecting the best available topology. **That limit is the power-systems problem.**
The conditional structure that governs process reconfiguration is not an artifact
of our modeling; it is what appears when $\tau_k$ ceases to be negligible.

In the reference plant of this study the dominant transition timescale is the
residence time of the drying train, on the order of a day. Disruptions of
interest last from hours to weeks. The ratio $\tau/D$ is therefore of order one,
not of order $10^{-6}$ as it is for a breaker operating against a daily load
curve. Empirically, this produces options whose breakevens are 33.5 h and 51.0 h
(Section 5), meaning they are net harmful on short disruptions and valuable on
long ones. No DNR formulation can represent an option with that property, because
no DNR formulation has a variable in which to express it.

This is the contribution boundary, and it is worth stating plainly rather than
implying it: the machinery of online topology reconfiguration is borrowed, and
gratefully. What is new is the regime where the transition is slow enough to
change the decision, the model structure required to decide in that regime, and
the resulting conditional economics.

## 2.4 Reconfigurable manufacturing systems: the closest neighbour on transition cost

Among adjacent fields, reconfigurable manufacturing systems (RMS) come nearest to
treating reconfiguration time as decision-relevant. Since Koren et al. (1999), the
RMS literature has held that reconfiguration cost and lead time are first-order
concerns, and subsequent work integrates reconfiguration cost into multi-period
capacity design and evaluates reconfiguration schemes by the resources and lead
time the reconfiguration itself consumes.

The distinction is one of timescale and trigger. RMS reconfiguration is a
planning decision, evaluated against evolving demand over months, in which the
reconfiguration is executed as a project. The present problem is an operational
decision, triggered by a disruption that has already begun, in which the
reconfiguration must complete while the disruption is still underway or it is
worthless. The RMS literature asks whether a reconfiguration is worth its cost;
this work asks whether it is worth its *duration*, given a disruption of unknown
remaining length, and whether the plant can physically reach the target state in
time. The former is an investment question, the latter a reachability question.

## 2.5 Infrastructure networks with genuine transients

Two infrastructure domains have real dynamics and are therefore closer physically
than power systems. Water distribution networks change topology under failure and
contamination through isolation-valve operation, and the literature recognizes
that valve closure alters the hydraulic equilibrium and induces flow reversals and
velocity surges. Optimization there addresses valve placement and closure
sequencing. Gas pipeline networks are modeled with full compressible transients,
and optimal control of transient flow (Zlotnik et al., 2015) and dynamic
compressor optimization are established problems, including formulations with
compressor mode switching.

Neither field gates an online topology decision on whether the transition can
complete before the disrupting event ends. In water networks the transient is a
consequence to be managed after the valve decision; in gas networks the transient
is the object of control but the network structure is fixed. The composition
studied here, a topology decision whose feasibility depends on the transient it
induces relative to the duration of the disruption that prompted it, does not
appear in either.

## 2.6 Flexibility, operability, and resilience in process systems

Within process systems engineering, three lineages bear on this work and none
occupies its position.

**Flexibility analysis** (Halemane and Grossmann, 1983; Swaney and Grossmann,
1985; Grossmann and Floudas, 1987) asks whether a fixed design can operate
feasibly across an uncertainty set, and produces an index of that capability. It
is a design-time, steady-state question about a fixed structure.

**Operability and switchability** (Vinson and Georgakis, 2000; Georgakis et al.,
2003) ask whether a plant can move between operating points and reach desired
outputs. Switchability in this sense concerns transitions between operating points
of a fixed flowsheet. The present work asks about transitions between
*flowsheets*, which is a different object: the graph itself changes, and with it
the model, the constraint set, and the reachable state space.

**Resilience-aware design** is the closest and most recent. Chrisandina et al.
(2024) survey resilience metrics for process systems, and Chrisandina et al.
(2025) introduce a Combined Flexibility-Resilience Index defined as the likelihood
that a system remains feasible under an uncertainty and disruption set. That index
and the present work are complementary in a way worth making explicit, because a
reader who knows the CFRI will otherwise see overlap. **The CFRI is a design-time
probability that a system can absorb a disruption. The breakeven developed here is
an operational probability that a disruption will outlast the response.** One
sizes the system before the event; the other decides what to do during it, and
supplies the condition under which acting is better than waiting. A plant designed
to a high CFRI may still be reconfigured harmfully if the disruption ends before
the transition completes, and that failure mode is invisible to a design-time
index.

## 2.7 Transitions as costed decisions, and the mathematical cousin

Two further literatures establish that "transitions cost enough to change the
decision" is not itself a novel proposition, which usefully narrows what this
paper must claim.

In process operations, **grade-transition dynamic optimization** (Cervantes et
al., 2002; Kadam et al., 2007; Flores-Tlacuahuac and Biegler, 2008) optimizes a
transient during which off-specification product accumulates, against a DAE model
of the plant. This is the direct PSE precedent for treating a transition as a
costed trajectory rather than an instantaneous jump. **Scheduling with
sequence-dependent changeovers** (Méndez et al., 2006; Harjunkoski et al., 2014)
similarly treats transitions as consuming real capacity. Neither, however,
attaches the transition to a topology decision or derives a threshold on an
exogenous disruption duration.

The nearest mathematical relative lies outside engineering. In the economics of
irreversible investment, sunk switching costs generate a **band of inaction**
between entry and exit triggers, so that an agent optimally refuses to act over a
range of states in which naive comparison would say to act (Dixit, 1989; Dixit and
Pindyck, 1994). The breakeven $D^{*}$ is structurally the same phenomenon: a
region of the state space in which the correct action is to do nothing despite an
apparently favorable comparison. The difference is the source and the gate. In
Dixit's setting the inaction band arises from a *sunk financial cost* and is
crossed when a *price* moves; here it arises from the *duration of a physical
transition* and is crossed when the *expected remaining disruption* is long
enough, subject to a dynamic reachability condition that has no counterpart in the
economic problem. The economics supplies the shape of the result; the physics
supplies its content.

## 2.8 What remains unclaimed

Assembling the boundaries above, the following appears to be open, and is what
this paper claims:

1. A **breakeven duration** for topology reconfiguration, derived in closed form
   from transition time, switching cost, and rescue margin, with the explicit
   result that it vanishes in the instantaneous-switching limit that defines the
   power-systems formulation.
2. The consequent **conditional structure of reconfiguration value**, including
   options that are net harmful on short disruptions and valuable on long ones,
   which is empirically confirmed and which the adjacent literatures cannot
   express.
3. A **decision architecture for that regime**: online detection, learned
   screening of a combinatorial change space, exact selection, and verification
   that the selected transition is dynamically reachable. The novelty is not the
   individual engines, each of which has precedent, but the reachability gate
   that the slow-transition regime makes necessary.
4. A **regional design criterion** in which the value of the capability is the
   product of plant economics and the probability that regional disruptions
   outlast the plant's breakeven, making the disruption climatology of a specific
   environment a quantitative input rather than a case-study backdrop.

Claims 1 and 2 are the paper's core. Claim 3 is engineering that follows from
them. Claim 4 is what makes the result actionable somewhere in particular.

---

## Appendix to this section: verification status

Citations added for this positioning carry explicit verification flags in
`references.bib`. Guo et al. (2025) was read in full from the publisher record and
is marked CONFIRMED; the characterizations in Section 2.2 (objective, horizon
discretization, switching-count constraint, and the role of the graph attention
network as an actor-critic approximator) are taken directly from that text. The
remaining entries are assembled from secondary listings and are marked VERIFY;
page ranges and DOIs must be checked against publisher records before submission.
Two are known to need attention: the Baran and Wu page range differs across
listings, and the volume number recorded for Chrisandina et al. (2024) is
inconsistent with the journal's numbering and may be wrong.
