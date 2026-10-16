# Autonomous mode

Same pipeline, executed through a provider.

```bash
cp .env.example .env   # fill OPENAI_API_KEY / OPENAI_BASE_URL / INTUITION_MODEL
intuition run --id myexp --provider openai_compatible --autonomy 2 --max-calls 30 --solvers 3
intuition resume --id myexp --provider openai_compatible --yes
```

Autonomy levels: 0 manual, 1 assisted (propose + approve), 2 supervised (auto-run, pause at
`reveal_original`, `accept_analogy`, `extra_calls`, `overspend`), 3 autonomous (bounded; still
gates `reveal_original`/`overspend` unless `--yes`).

Safety: max iterations / model-call / token / time budgets; stopping on cancellation, no-progress,
candidate-proof (-> verification, not success), counterexample, or critical gap. Interrupted runs
resume without repeating completed expensive calls. Provider errors (rate limits, network, malformed
output) are logged as events; the run stops cleanly instead of fabricating results.

Secrets come from env/`.env` (git-ignored) and are never written into experiment records.
Without credentials, the CLI directs you to manual mode. `mock` provider is offline/deterministic
and must never be presented as empirical evidence.
