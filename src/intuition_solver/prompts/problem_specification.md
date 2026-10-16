# Problem Specification Prompt (template version: v1)

You are helping a researcher produce a rigorous structured specification of a mathematical problem.
Do NOT solve the problem yet. Do NOT invent missing definitions. Flag gaps explicitly.

## Researcher-supplied material
$PROBLEM_INPUT

## Produce a structured specification with these sections
1. Problem statement (verbatim, then a cleaned restatement clearly marked as interpretation).
2. Definitions and notation (symbol, meaning, source).
3. Explicit assumptions (numbered A1, A2, ...).
4. Desired theorem or conclusion (formal claim C).
5. Known results and literature supplied by the researcher (with sources; mark "not verified here").
6. Constraints on acceptable solutions (e.g. elementary only, no choice, finite case only).
7. Existing partial results and previously attempted approaches.
8. Research objective (what would count as progress, not just "solve it").
9. Required proof obligations (numbered P1, P2, ...; every step that must be discharged).
10. Epistemic ledger: Established facts | Assumptions | Conjectures | Open questions (keep these disjoint).

## Objective tracker
Also produce an Objective Tracker block:
- ORIGINAL_GOAL: ...
- CURRENT_SUBPROBLEM: ...
- PROGRESS: ...
- UNRESOLVED_OBLIGATIONS: ...

Rules: distinguish facts from conjectures; never silently change the problem;
list anything you could not determine under "UNRESOLVED".
