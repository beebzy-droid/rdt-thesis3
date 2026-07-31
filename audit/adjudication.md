# Adjudication of Inter-Rater Disagreements

*Two independent raters, seven papers, six protocols, 42 cells. Pooled Cohen's
kappa 0.818, 95% CI [0.68, 0.94]. Six cells disagreed. Each is resolved below with
the reasoning recorded, and the rubric amended where the disagreement exposed an
ambiguity rather than a reading error.*

## The pattern matters more than the count

Five of the six disagreements are **S versus P**: both raters saw the same
practice and differed on whether it fully satisfied the protocol or partly
satisfied it. Not one disagreement was about whether a practice was a *problem*.

Agreement on the codes that carry the audit's claims is near-perfect. P5 reached
kappa 1.000: the raters never disagreed about whether re-initialization was
reported. P6 was degenerate, both raters assigning Not Applicable to every paper,
which is the finding that prescriptive studies assume disruption is known. The
Violated and Not Reported codes, which is where the audit's conclusions live, were
assigned consistently.

**The instrument identifies problems reliably and grades degrees of compliance
unreliably.** That is worth stating plainly, because it bounds what the audit can
claim: the counts of Not Reported and Violated are trustworthy, and any finer
ranking of which papers evaluated *best* is not.

## Resolutions

**A1, protocol 2. Rater 1 NR, rater 2 NA. Resolved: NR.**
The controller acts repeatedly across a multi-step restoration episode, so
recurrence exists and the protocol applies; no comparison isolating it appears.
NA is reserved for systems making a single decision per scenario. *Rubric amended
to say so explicitly.*

**A1, protocol 4. Rater 1 P, rater 2 S. Resolved: P.**
The paper reports 95% confidence intervals over 504 test scenarios, which is
excellent practice and exactly the partial-credit case. It does not commit
hypotheses or endpoints in advance, which the S code requires. *This disagreement
recurred (see D2) and indicates a rubric defect, addressed below.*

**A2, protocol 1. Rater 1 P, rater 2 S. Resolved: P, with a new rule.**
Both readings were correct about different arms. The MLP-RL ablation is explicitly
symmetric, trained with the same settings; the MISOCP comparison is not, since the
optimizer solves a relaxed model while the learned method acts on the nonlinear
one. The rubric gave no rule for mixed-arm cases. *Amended: score the arm carrying
the headline claim.* Here that is the exact-optimum comparison, so P.

**C1, protocol 3. Rater 1 P, rater 2 S. Resolved: NA, neither original code.**
Adjudication found both raters wrong. Protocol 3 concerns bounding an alternative
that was *not implemented*. Hajgato et al. implement and run their comparators, so
there is no unbuilt alternative to bound. That is a protocol-1 matter, not a
protocol-3 one. *The rubric conflated bounding an unimplemented alternative with
providing a performance ceiling; these are different and are now separated.*

**D2, protocol 4. Rater 1 P, rater 2 S. Resolved: P.**
Same boundary as A1. The paper reports an honest negative about its own method's
degradation under distribution shift, which is the partial case, not advance
commitment.

**E3, protocol 1. Rater 1 P, rater 2 S. Resolved: S.**
Rater 1's confidence here was medium, resting on partial text; rater 2 read the
full paper and found the comparison against PPO, a topology baseline, and Random
run in a shared environment. The protocol in `audit/README.md` gives the
presumption to the rater who read the full text.

## Rubric amendments arising

1. **Protocol 2, NA clarified.** NA applies only when the system makes a single
   decision per scenario. A policy acting repeatedly within an episode has
   recurrence to justify, whether or not a single-shot variant is available.
2. **Protocol 4, S/P boundary sharpened.** S requires evidence of advance
   commitment: a registry entry, timestamp, or version-controlled hash. Confidence
   intervals, repeated seeds, and honest negatives are P however well executed.
   Three of six disagreements arose here; the protocol's name invited reading it
   as a general statistical-rigor score, which it is not.
3. **Protocol 1, mixed arms.** Where a study uses several comparators of differing
   symmetry, score the arm carrying the headline claim, and record the others in
   comments.
4. **Protocol 3, scope separated from performance ceilings.** The protocol asks
   whether an *unimplemented* alternative was bounded rather than asserted to be
   inferior. A ceiling computed on the proposed method's own problem, and a
   comparator that was actually built and run, are different things and are no
   longer conflated.

## Consensus effect on the audit

None of the four headline findings changes. Recurrence justification remains
absent across the corpus; re-initialization remains unreported or instantaneous
with perfect rater agreement; bounding remains rare but achievable; detection
remains unscoreable for the reason that is itself the result. The resolutions move
three cells between S and P, one from P to NA, and confirm two.
