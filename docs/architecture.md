# Architecture

Single shared pipeline serves both modes:

```
Problem spec -> Analogy (+ blind/audit prompts, leakage check) -> Independent solvers (isolated)
  -> Cross-examination (peer info ONLY here) -> Reconstruction (original revealed)
  -> Verification (human/Lean-gated PROVEN) -> Report / comparison
```

- `core/`: validated Pydantic models + events (single source of truth).
- `prompts/`: versioned Markdown templates (`prompts/__init__.py: render()`).
- `agents/`: prompt builders + section parsers (roles are prompt configs, not necessarily separate models).
- `providers/`: `BaseProvider` interface; `mock` (offline/tests) + `openai_compatible` (stdlib HTTP + optional `openai` SDK).
- `workflows/manual.py`: researcher-operated, no API key; append-only imports.
- `workflows/autonomous.py`: same stages via provider; budgets, gates, resume without repeating calls.
- `workflows/budgets.py`, `checkpoints.py`, `stages.py`: shared safety logic.
- `evaluation/`: metrics, baselines A-D, comparison (with limitation flags), Markdown/JSON reports.
- `verification/`: finite-case runner, optional sympy/Lean hooks. Finite passes yield at most COMPUTATIONALLY_SUPPORTED.
- `storage/`: `experiments/<id>/experiment.json` + `events.jsonl`; anonymized export strips secrets.
- `cli/` (Typer) and `web/` (FastAPI) are thin views over the same workflows.

Key invariants:

1. Blind solvers never receive the original statement/notation/title (leakage checker + audit gate; heuristic only).
2. Independence: peer responses enter only at cross-examination; every exposure is event-logged.
3. Raw records are never overwritten; summaries live separately.
4. A model alone can never confer PROVEN. Human sign-off or an actually-run Lean check is required.
5. Agreement is not proof; confidence is not evidence; finite tests are not unrestricted proof.
