# Reframe Status: What Six Experiments Established, and What Follows

*2026-07-13. Written after the second reframe attempt returned a null. Its purpose
is to record honestly what this simulator can and cannot support, so that the
manuscript claims only what survived testing.*

## The tally

| # | Claim tested | Outcome |
|---|---|---|
| 1 | Gain saturates beyond the evaluation horizon (Cor. 1.1) | **CONFIRMED**, slope ratio 0.000 |
| 2 | Breakeven identifiability tracks rescue margin | **CONFIRMED**, unidentified cells are exactly the near-zero-margin ones |
| 3 | $dD^{*}/d\tau = 1$, control-input options | null: those options bypass the dryer |
| 4 | $dD^{*}/d\tau = 1$, topology option adding dryer capacity | null: additive option, $c \approx 0$ |
| 5 | $dD^{*}/d\tau_{\text{com}} = 1$, substitutive option | null: the gate delays effect, not value |
| 6 | Buffer scales the breakeven (constraint-activation mechanism) | directional at the small end, saturating and underpowered |
| 7 | Perishability forecloses the buffering strategy | **null, and the design is invalid** |

Experiment 7 failed for an instructive reason. Pre-positioned inventory was
implemented by scaling the initial copra holdup, but the press draw is
$F_{\text{press}} \propto I_{\text{copra}}/\tau_{\text{buf}}$, so a larger initial
stock forces over-drawing, fills the crude tank, trips the `gate_tank` throttle,
and inflates the pre-disruption baseline against which resilience is normalized.
Resilience therefore *falls* monotonically with buffer size, from 0.584 at nominal
to 0.348 at thirty times nominal. That is a perturbation of the operating point,
not a buffering strategy, and no conclusion about perishability can be drawn from
it. Testing buffering properly requires designed capacity with a matched draw
policy, which is a different plant model.

## What this means

The simulator was built to answer one question well, and it does: **does runtime
topology reconfiguration improve resilience, and is that improvement real against
a hard comparator?** Every result bearing on that question has held up under
adversarial testing. What the simulator does not contain is the structure needed
to support mechanistic claims about *why* the conditional value arises: it has no
transition-cost representation (experiments 3 to 5) and no buffer-design
representation (experiment 7). Each reframe attempt has required model surgery,
and each round of surgery brings the work closer to fitting the plant to the
theory rather than the reverse.

The correct response is to stop searching for a grand mechanism and to claim what
was actually established.

## What is established and survives every test

1. $\Delta R = 0.244$, CI $[0.237, 0.251]$, over 2,000 pre-registered paired runs
   against a hardened symmetric static comparator.
2. $\Delta R = 0.294$, CI $[0.286, 0.302]$, against an optimistic clairvoyant bound
   on any continuous controller over the same action set. The margin is *wider*
   than the headline, so a stronger continuous comparator does not erode the
   advantage.
3. A recurrent loop with an imperfect screen (0.190) beats its own one-shot
   perfect-foresight oracle (0.187).
4. Comparator asymmetry manufactures false negatives: 0.117 with asymmetric arms
   against 0.241 with symmetric arms, on the same scenarios.
5. Pre-registration caught a *model* artifact, the uncapped purchase market, that
   a post-hoc analysis would plausibly have rationalized.
6. Hot-starting newly activated units understates the reconfiguration breakeven
   three- to fourfold relative to a cold-start commissioning contract.
7. Detection delay is net positive under a hoard-then-deploy policy, so the cost
   of latency is a property of the policy it gates rather than of the detector.
8. Graph-attention screening does not transfer to unseen reconfigurations at the
   reachable data scale, reported with paired baselines and a documented floor.
9. TTR$_{80}$ falls 57.7%, CI $[55.2, 60.2]$, as a floor estimate.

## The contribution that follows

Items 3 through 8 are not results about a coconut plant. They are results about
**how to evaluate a prescriptive digital twin**, and each was demonstrated
empirically rather than asserted:

- evaluate against a *symmetric* comparator or measure the wrong thing;
- benchmark a closed loop against its own one-shot oracle to test whether
  recurrence earns its complexity;
- bound the continuous-control alternative rather than arguing about it;
- pre-register, because it catches model errors and not merely analyst bias;
- model re-initialization honestly, because hot-starting flatters the decision by
  a factor of three;
- evaluate detection inside the policy it gates, not against a delay objective.

That set is transferable, falsification-resistant, and unclaimed as a package. It
is also, unlike every mechanism claim attempted here, supported by evidence
already in hand. The recommended framing is an evaluation-methodology paper for
prescriptive digital twins, demonstrated on runtime topology reconfiguration under
typhoon-calibrated disruption, with the resilience result as the worked example
rather than the thesis.
