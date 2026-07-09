# Reviewer Report — RDT Thesis III / CCE Paper 1

*PM/reviewer pass, 2026-07-04. Role: the reviewer this manuscript would be
assigned. Verdict up front, then findings by severity. This is a red-team read,
not a validation — the author's own read is sound; my job is what Reviewer 2
hits first.*

## Verdict

**Scientifically: accept-grade with major-revision conditions, all closable.**
The core is genuinely novel (topology as a runtime state variable of a
physics-consistent twin — the three-literature gap is real and the systematic
search backs it), the headline result is statistically hard (2,000 paired runs,
pre-registered, ΔR CI-excluding-target under two market regimes), and the
integrity posture (synthetic labels, provenance gate, negative result reported)
is stronger than the median CCE submission. The conditions below are about
**one blocking gap** and a set of framing/format items — not about the science.

**Journal fit: strong and confirmed.** CCE's stated major areas include
mathematical programming (optimization), process dynamics/control/monitoring,
abnormal events management and process safety, and plant operations/planning/
supply chain — the RDT hits four of them, and "general papers on process systems
engineering are welcome" covers the integration. This is a native CCE paper, not
a stretch. (Fit verified against the current aims & scope, 2026-07.)

## Blocking (must close before submission)

**B1 — The economic claim rests on 0/30 verified parameters, and freq_D4
(54% of the E11 total) is a pure [verify].** A reviewer will not accept
"₱86–101 M/yr" and "payback < 2 months" as headline abstract claims when the
provenance gate is red. *This is not a modeling flaw — the machinery is honest —
but it is a submission blocker for Paper 2 (RESS, impact-focused) and a liability
even in Paper 1.* Resolution options, in order of preference:
  (a) Verify the Tier-1 rows (freq_D4, φ, w_vco, w_copra_buy, w_crude) before
      submission — the register already names the sources.
  (b) If (a) can't complete in time: **demote all PHP figures from the abstract
      and headline to a clearly-scoped "indicative economics" subsection**, and
      lead with the dimensionless ΔR/TTR₈₀ results, which are fully defensible
      today. Paper 1 (CCE, methodology) can carry the economics as illustrative;
      Paper 2 (RESS) cannot and must wait for (a).
  My recommendation: **(b) for Paper 1 now, (a) gating Paper 2.** The methods
  paper does not need verified pesos; the impact paper is nothing without them.

## Major (address in revision; each is a likely reviewer comment)

**M1 — H6 (≤60 s cycle) is claimed "met" but is not measured.** §6.4/§7.6 are
honest that the 0.5 h grid floors detection delay and that the 60 s target "lives
at production sampling." A reviewer will read the H6 row of the adjudication
table ("Met in-sim") as overclaiming, because the *cycle* was never run at
production rates. **Fix:** restate H6 explicitly as *not tested* — "compute-time
budget met with >10³ margin; end-to-end latency at production sampling is future
work (§7.6)." Do not leave a checkmark next to H6. Honesty here is free and
pre-empts a credibility ding that would spill onto H4/H5.

**M2 — The strong baseline is fixed-schedule; the MPC-lite comparator is named
but not built.** §7.6 owns this, which helps — but a sharp reviewer will ask
"how much of your 0.244 survives against a receding-horizon continuous
controller?" The current answer ("bounded but nonzero erosion, ≥90% of scenarios
hoard→deploy already dominates") is *argued*, not *shown*. **Fix options:** (a)
build the MPC-lite arm (the honest close — but scope/time cost); or (b)
strengthen the argument with a bounding calculation: the maximum ΔR a perfect
continuous controller could reclaim is capped by the gap between hoard→deploy and
the *clairvoyant* continuous optimum on the same paths, which you can compute
offline without building the controller. I'd do (b) as a bounding paragraph — it
converts an assertion into an inequality with numbers, which is what the reviewer
wants, at a fraction of (a)'s cost.

**M3 — N=7 wired options of a 19-edge candidate set.** The novelty claim is
"topology reconfiguration," but only 7 of 19 candidate edges are physically
modeled in the compiler. A reviewer will ask whether the result is an artifact of
which 7 were chosen. **Fix:** one paragraph in §5/§6 stating the selection
rationale (the 7 span the rescue/harmful/near-zero value classes — you have this
in F#17, it just needs to be surfaced as a deliberate design choice, not an
implementation limit) and an explicit statement that extending to the full 19 is
mechanical, not conceptual.

**M4 — Single plant archetype.** Standard external-validity comment. §7.6 lists
it. **Fix:** sharpen the transferability argument — the *method* (layered
screening over a physics graph) is plant-agnostic; the ICPC is the demonstration.
One sentence in the abstract's contribution list and a §7.7 paragraph. The
open-source release is your strongest rebuttal here (others can run their own
plant) — lean on it.

## Minor (polish; reviewers notice these)

- **m1 — Title.** CCE has no "novel/first" prohibition (that's JACS), so "first"
  is defensible — but two Elsevier reviewers in three will flag a title starting
  with the method over the finding. Consider testing a finding-forward variant.
  Not blocking.
- **m2 — Abstract length.** 1,435 words for the *combined* front matter is fine,
  but the standalone abstract paragraph must land ≤250 words for CCE; verify the
  extracted abstract hits it. Currently ~310 in the three-paragraph block.
- **m3 — The recurrent-beats-oracle result (F#19) is buried.** This is arguably
  the most novel *conceptual* point (imperfect-repeated > perfect-once) and it's
  in §7.2 as a mechanism note. **Promote it** — it belongs in the abstract's
  "three results" and possibly its own short results subsection. Reviewers reward
  a crisp conceptual takeaway; this is yours.
- **m4 — Figure count.** 9 figures is at the upper end for a single CCE paper
  (~10-12 is the informal ceiling with SI). If splitting Paper 1/2, F1-F3 (ΔR)
  and F7 (hardening) anchor Paper 1; F4 (TTR), F6 (detection) partly to Paper 2.
  F9 (N2 negative) is Paper 1. Plan the figure allocation with the split.
- **m5 — Reproducibility is a selling point; state it in the cover letter.** The
  one-command harness + determinism gate + provenance ledger is above-median for
  the field. CCE reviewers increasingly weight this. Make it explicit.

## What is genuinely strong (keep, and lead with)

1. The pre-registration catching a *model* artifact (the missing inverted-U →
   uncapped-purchase unrealism, F#25) is a genuinely sophisticated methods point.
   Few PSE papers demonstrate pre-registration at all, fewer show it *working*.
2. The comparator-symmetry false-negative (F#21) is a transferable protocol
   contribution — pull it out as a named subsection; it will be cited.
3. The negative N2 result with paired controls and a scale floor is exactly the
   honesty reviewers claim to want and rarely get. It also de-risks the paper: no
   one can say the GAT claim is overstated, because you understated it yourself.
4. The φ-robustness of H4 (target held under a 3× market haircut) is the single
   strongest defensive result — a reviewer's instinct is to attack the effect
   size; you've already shown it survives the obvious attack.

## Suggested pre-submission sequence

1. Close **B1** (verify Tier-1 or demote pesos — decide per paper).
2. Fix **M1** (H6 restatement) and **M3** (option-selection paragraph) — both are
   one-paragraph edits, high credibility-per-word.
3. Add **M2(b)** bounding calculation — converts the baseline objection to numbers.
4. Promote **m3** (recurrent-vs-oracle) and **F#21** to their deserved prominence.
5. Extract and length-check the standalone abstract (**m2**).
6. Cover letter leads with fit (four CCE areas), reproducibility, and the
   pre-registration/negative-result integrity posture.

None of items M1–M4 or m1–m5 threaten the core claims. B1 is the only true gate,
and it is a *verification* task, not a *research* task — the science is done.
