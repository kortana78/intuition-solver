# Analogy Audit Prompt (template version: v1)

You are auditing an analogy BEFORE it reaches blind solvers. You may see both the original
problem and the analogy. Be strict: a leaky or unfaithful analogy is worse than none.

## Original problem
Title: $PROBLEM_TITLE
Statement: $PROBLEM_STATEMENT
Notation/identifiers: $FORBIDDEN_TERMS

## Candidate analogy
$ANALOGY_STATEMENT
Correspondence: $CORRESPONDENCE
Must preserve: $PRESERVED
Lost/approximate: $LOST
Introduced assumptions: $INTRODUCED_ASSUMPTIONS

## Audit tasks
1. LEAKAGE CHECK: does the analogy text reveal the original field, conjecture/problem name,
   original notation, or title keywords ($FORBIDDEN_TERMS)? Quote any leak verbatim.
2. FIDELITY CHECK: does the correspondence map cover every proof obligation ($PROOF_OBLIGATIONS)?
   Which obligations have no counterpart?
3. PRESERVATION CHECK: are the MUST_PRESERVE properties actually preserved by the construction?
4. ASSUMPTION CHECK: do INTRODUCED_ASSUMPTIONS smuggle in extra strength that trivialises or
   falsifies the analogy?
5. INVALIDATION: answer each INVALIDATING_QUESTION ($INVALIDATING_QUESTIONS) with keep / fix / drop.
6. VERDICT: APPROVE (blind-safe), FIX (list exact edits), or DROP (give reason).

Note: automated string checks are heuristic only and cannot guarantee semantic concealment.
Human judgement is required before export.
