# Mathematical Reconstruction Prompt (template version: v1)

The original mathematical problem is NOW revealed to you. Your job is to translate selected
analogy insights back into rigorous mathematics, and to REJECT transfers that do not survive.

## Original problem specification
Title: $PROBLEM_TITLE
Statement: $PROBLEM_STATEMENT
Definitions: $DEFINITIONS
Assumptions: $ASSUMPTIONS
Desired theorem: $DESIRED_THEOREM
Proof obligations: $PROOF_OBLIGATIONS

## Analogy + correspondence
Analogy ($ANALOGY_DOMAIN): $ANALOGY_STATEMENT
Correspondence map: $CORRESPONDENCE
Must preserve: $PRESERVED | Lost: $LOST | Introduced: $INTRODUCED_ASSUMPTIONS

## Solver outputs + dialogue (summaries; raw records retained in experiment)
$SOLVER_SUMMARIES
$DIALOGUE_SUMMARIES

## Researcher-selected insights to attempt
$SELECTED_INSIGHTS

## For EVERY transferred idea, output exactly
- CLAIM: precise mathematical statement.
- ASSUMPTIONS: everything it depends on (original + translation-introduced).
- MOTIVATED_BY: which analogy insight suggested it (quote).
- DERIVATION: proposed mathematical derivation, step by step.
- TRANSFER_VALID: yes / no / uncertain + justification (does the analogy actually justify this step?).
- MISSING_LEMMAS: numbered open lemmas.
- PROOF_OBLIGATIONS: which of $PROOF_OBLIGATIONS it discharges, if any.
- COUNTEREXAMPLES_OR_ISSUES: known or suspected problems.
- STATUS_SUGGESTION: proven / computationally-supported / conjecture / gap / refuted / known-result / unverified
  (a suggestion only; final status requires the verification pipeline + human review).

You MUST reject attractive ideas whose transfer is invalid. Say REJECTED + reason.
Never present finite tests as proof of an unrestricted statement.
