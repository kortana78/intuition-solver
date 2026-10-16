# Experimental protocol

## Conditions
- A: direct single-model. B: direct multi-model. C: analogy, no dialogue. D: full architecture.

## Controls
Same underlying models/versions, comparable budgets, same problem set, same rubric.
Log every deviation (model swap, extra calls, prompt edits) as an experiment event/note.

## Problem sets
- Solved: correctness + transfer precision (expect PROVEN only with human/Lean sign-off).
- False conjectures: counterexample detection rate (REFUTED with concrete instance).
- Open: exploratory only: record insights as CONJECTURE/GAP; never claim solutions.

## Recording
Use `intuition baseline --condition ... --file ...` per condition; researcher assessment +
evidence required. `intuition evaluate --compare` refuses conclusions from incomplete data.

## Stopping
Pre-register budgets; stop on exhaustion, candidate-proof (-> verify), counterexample, or gap.
Report all runs, including failures.
