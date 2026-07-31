# Scoring Rubric: Six Evaluation Protocols

*Instrument v1, 2026-07-13. For the audit reported in Section 7 of the RESS
manuscript. Designed to be applied from a published methods and experiments
section alone, without contacting authors and without access to code.*

## How to use this

Read the paper's methods and experiments sections. For each protocol, assign one
code. Do not infer beyond what the text states. If you find yourself reasoning
"they probably did X," the correct code is **NR**, not the code for X.

The single most important rule: **NR is not a criticism.** Most of these protocols
are not current convention, and page limits are real. NR records that a reader
cannot tell from the paper, which is a fact about the reporting, not about the
research.

## Codes

| Code | Meaning |
|---|---|
| **S** | Satisfied. The paper states it did the thing. |
| **P** | Partial. The paper does part of it, defined per protocol below. |
| **V** | Violated. The paper states something that contradicts the protocol. |
| **NR** | Not reported. Cannot be determined from the text. |
| **NA** | Not applicable. The protocol presupposes a feature this system lacks. |

## P1. Comparator symmetry

*Question: do the compared arms differ in exactly one factor, that factor being
the treatment?*

- **S** The paper states that arms share the environment, objective, and
  underlying policy apart from the treatment, or describes both arms in enough
  detail for a reader to verify no capability or information asymmetry. Phrases
  like "identical action space, reward, and objective" are sufficient.
- **P** A strong, tuned comparator is used (optimized policy, exact method,
  operator heuristic) but arm-level symmetry is not verifiable from the text.
- **V** The paper describes an asymmetry: arms evaluated on different plant
  models, one arm given information withheld from the other, or a baseline left
  untuned while the proposed method is tuned. Score V whether or not the authors
  disclose it; disclosure is noted separately in the comments column.
- **NR** A baseline exists but neither arm is described in sufficient detail.
- **NA** No comparative performance claim is made.

*Two common cases worth flagging, both scored* **V**:

1. A learned method interacting with a nonlinear simulator, compared against an
   optimizer solving a linearized or relaxed model, with both scored on the
   nonlinear model.
2. **The baseline doubles as the training signal.** The proposed method is
   trained toward the baseline's outputs, or rewarded for matching them, and is
   then evaluated against that same baseline. The comparison is not independent:
   the treated arm cannot substantially exceed its own teacher, so a reported
   ratio near unity is close to tautological. This case was added after reading a
   study in the audit corpus where it occurs, and it is easy to miss because the
   baseline is genuinely strong and the reporting is otherwise careful.

## P2. Recurrence justification

*Question: if the system re-decides over time, is re-deciding shown to help?*

- **S** The paper compares its closed-loop system against a single-shot,
  open-loop, or one-decision variant of the same system.
- **P** The paper compares against another closed-loop method in a way that
  isolates the recurrence mechanism.
- **V** The paper asserts that recurrence is the source of the benefit without
  any comparison isolating it.
- **NR** A closed loop, rolling horizon, or repeatedly-acting policy is proposed
  and no such comparison appears.
- **NA** The system makes a single decision per scenario, so there is no
  recurrence to justify.

## P3. Bounding the unbuilt alternative

*Question: is an alternative approach bounded rather than asserted to be worse?*

- **S** The paper reports an oracle, perfect-foresight, exact-optimum, or
  relaxation bound and compares against it.
- **P** A bound exists but is on the proposed method's own model rather than on
  an alternative approach (for example a robust worst-case, or a convex
  relaxation whose gap is not quantified).
- **V** The paper claims an unimplemented alternative would perform worse, with
  no bound or evidence.
- **NR** No alternative approach is discussed.
- **NA** No alternative is plausible for the problem as posed.

## P4. Pre-registration

*Question: were analysis choices committed before seeing results?*

- **S** Hypotheses, endpoints, thresholds, or an analysis plan were committed in
  advance, evidenced by a registry entry, timestamp, or version-controlled commit.
- **P** Practices that pre-registration would formalize are present: interval
  estimates over multiple seeds or runs, repeated experiments explicitly to
  separate systematic effects from noise, or an honest negative reported about
  the authors' own method.
- **V** The paper describes selecting metrics or thresholds after inspecting
  results.
- **NR** None of the above.

## P5. Re-initialization

*Question: when the system activates an element, how does that element start?*

- **S** The paper states the initialization contract for activated elements
  (ramp, fill, commissioning delay, warm or cold start) **and** reports a
  sensitivity analysis on that choice.
- **P** The contract is stated but no sensitivity is reported.
- **V** The paper states that activated elements contribute at full capability
  immediately, with no acknowledgment that this is an assumption.
- **NR** Elements are activated and the text is silent on their initialization.
- **NA** The system does not activate, commission, or bring online any element.

## P6. Detection inside its policy

*Question: if a detector gates the response, are its actual delays charged to the
end-to-end outcome?*

- **S** A detector is inside the loop and end-to-end performance is reported with
  the detector's realized delays and false alarms in force.
- **P** A detector is in the loop but detection and outcome are reported
  separately, without an end-to-end run charging the delays.
- **V** Detection is optimized against a delay objective while an end-to-end
  benefit is claimed that the detection study does not support.
- **NR** A detector is present and its treatment is not described.
- **NA** No detector: disruption onset, fault location, or failure identity is
  assumed known.

*Note:* **NA** is expected to dominate in prescriptive resilience studies, and
that concentration is itself reportable. Record it rather than forcing a score.

## Recording

For each paper record: the six codes, and for any **V** a short quotation or
close paraphrase supporting it. A V without supporting text is not admissible and
should be downgraded to NR.
