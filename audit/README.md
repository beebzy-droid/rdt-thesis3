# Inter-rater reliability protocol

Section 7 of the RESS manuscript reports an audit of published evaluations. A
single-rater audit invites the objection that the scoring is subjective. This
directory holds the instrument for a blind second rating.

## Protocol

1. Rater 2 reads `rubric.md` and scores the papers in `scoring_sheet_BLANK.csv`
   from their published methods sections. Save as `scores_rater2.csv`.
2. **Do not open `scores_rater1_SEALED.csv` until step 1 is complete.** The
   blinding is the entire point; a rating anchored on the first rater's codes
   measures agreement with a prior, not agreement between raters.
3. Run `python scripts/interrater.py` to compute Cohen's kappa per protocol and
   overall, with a bootstrap interval.
4. Disagreements are resolved by discussion and the resolution recorded. Report
   both the pre-resolution kappa and the final consensus scores.

## What counts as adequate agreement

There is no universal threshold, and we do not intend to imply one. We will report
kappa with its interval and let a reader judge. For orientation, values around 0.6
to 0.8 are commonly described as substantial in the methodological literature, and
values below 0.4 would indicate the rubric is not operational enough to publish
and should be revised before the audit is reported.

## Honest note on the first rating

Rater 1's scores carry a confidence field. Two entries are marked high confidence
because their full methods sections were read closely; the rest are medium,
resting on abstracts and partial texts. Where rater 2 disagrees with a
medium-confidence score, the presumption should favour rater 2's reading of the
full text.
