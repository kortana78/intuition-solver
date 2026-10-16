# Intuition Solver

A unified research framework **and** autonomous multi-agent system for studying whether
**domain-obscured analogies** can improve AI-assisted mathematical exploration.

> **Hypothesis under test (not a conclusion):** separating problem representation from solution
> generation through domain-obscured analogies can produce useful mathematical insights that are
> less likely to emerge through direct problem-solving alone.

```
Problem spec -> Analogy (blind/audit + leakage check) -> Independent solvers (isolated)
  -> Cross-examination (peer info ONLY here) -> Reconstruction (original revealed)
  -> Verification (human/Lean-gated) -> Report / A-D comparison
```

Both operating modes share one pipeline, one prompt set, one data model, one verification ladder:

| | **Mode A: Research Framework** | **Mode B: Autonomous Agent** |
|---|---|---|
| Control | Human copies prompts into any 3+ AI tools, pastes answers back | Provider APIs run the same stages |
| Needs API key | **No** | Yes (or `mock` for offline smoke tests) |
| Autonomy | Level 0 manual | Levels 0-3 with budgets + approval gates |
| Command | `export-prompts` / `import-response` ... | `run` / `resume` |

**What this is not:** it does not claim to solve open problems or produce novel discoveries without
evidence. Ideas -> translation -> truth stay separate and auditable. See *Limitations*.

## Install

```bash
python --version  # 3.11+
pip install -e .
intuition --help
# web UI (optional): uvicorn intuition_solver.web.app:app --reload
```

`pip install -e ".[openai]"` enables the official SDK path (optional; stdlib HTTP fallback included).
Copy `.env.example` to `.env` for autonomous runs. Never commit `.env` or API keys.

## 5-minute manual tutorial (no API key, 3 external models)

```bash
intuition init --title "Even plus even" --id demo --statement "Prove the sum of two even integers is even."
intuition generate-analogy --id demo --domain "resource allocation"
# edit experiments/demo/experiment.json -> write a self-contained analogy, then:
intuition approve-analogy --id demo --analogy <an-id>
intuition export-prompts --id demo --analogy <an-id>   # copy solver-N_blind.md into 3 separate AI tools
# save answers to a1.md a2.md a3.md, then:
intuition import-response --id demo --analogy <an-id> --solver solver-1 --file a1.md --model "ModelA v1"
intuition import-response --id demo --analogy <an-id> --solver solver-2 --file a2.md --model "ModelB v1"
intuition import-response --id demo --analogy <an-id> --solver solver-3 --file a3.md --model "ModelC v1"
intuition cross-examine --id demo --analogy <an-id> --role critic --file c1.md
intuition reconstruct --id demo --analogy <an-id> --file recon.md --print-prompt
intuition audit --id demo --set <claim>=CONJECTURE --note <claim>="human: reason"
intuition report --id demo
```

Fully worked offline example (labelled illustrative responses): `python examples/solved_problem/run_demo.py`.

## Autonomous tutorial

```bash
cp .env.example .env  # set OPENAI_API_KEY / OPENAI_BASE_URL / INTUITION_MODEL
intuition run --id demo --provider openai_compatible --autonomy 2 --max-calls 30 --solvers 3
intuition resume --id demo --provider openai_compatible
intuition evaluate --id demo
intuition evaluate --compare   # A-D comparison with limitation flags
```

Budgets (`--max-calls`, token/time limits in config), gates (`reveal_original`, `accept_analogy`,
`extra_calls`, `overspend`), and stopping conditions (budget/iteration limits, cancel, no-progress,
candidate-proof -> verify, counterexample, critical gap) bound every run.

## Verification ladder

`PROVEN, COMPUTATIONALLY_SUPPORTED, CONJECTURE, GAP, REFUTED, KNOWN_RESULT, UNVERIFIED`.
A model alone can never confer `PROVEN` (code downgrades it); the CLI requires a `human:`/`lean:`
sign-off note. Finite passes yield at most `COMPUTATIONALLY_SUPPORTED`. Lean counts only when actually run.
Details: `docs/verification.md`.

## Evaluation

Conditions **A** direct-single, **B** direct-multi, **C** analogy w/o dialogue, **D** full architecture.
Record with `intuition baseline --condition ...`; compare with `intuition evaluate --compare`
(refuses conclusions from incomplete data). Metrics: validity breakdown, lemma counts, Jaccard
approach diversity, counterexample counts, cost. Protocol: `paper/experimental_protocol.md`.

## Repo map

`src/intuition_solver/{core,prompts,agents,providers,workflows,evaluation,verification,storage,cli,web}/`
`tests/{unit,integration,fixtures}/`, `examples/solved_problem/`, `experiments/` (git-ignored workspace),
`paper/` (outline + protocol + results template), `docs/`.

## Limitations

- Blind-mode leakage checks are heuristic string matches; human audit required; semantic concealment not guaranteed.
- Agreement is not proof; confidence is not evidence; finite tests are not general proof.
- Novelty needs documented literature review; references are never fabricated by the system.
- Autonomous runs cost money/time and inherit provider/model biases; `mock` outputs are placeholders, never evidence.

## Contributing / License

See `CONTRIBUTING.md`. MIT license: see `LICENSE`.
