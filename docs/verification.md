# Verification

Statuses: `PROVEN, COMPUTATIONALLY_SUPPORTED, CONJECTURE, GAP, REFUTED, KNOWN_RESULT, UNVERIFIED`.

- Human audit (`intuition audit`) assigns the **final** status. Model triage text is advisory only;
  `VerifierAgent.suggest_status()` downgrades any model-claimed PROVEN to UNVERIFIED.
- CLI enforces: `--set <claim>=PROVEN` requires a `--note` containing `human:` or `lean`.
- Finite-case checks (`--finite file.py --claim <id>`): passing N cases yield at most
  COMPUTATIONALLY_SUPPORTED for the tested range, never proof of an unrestricted statement.
- Symbolic (`try_symbolic`) needs sympy; Lean (`try_lean`) shells to `lake env lean` **only if
  installed**; otherwise it reports *skipped, not verified*. Formal claims require an actual run.
- Independent review: import a separate model's audit as a dialogue turn with role `critic`.
- Novelty is separate: new-to-experiment / not-checked / known / potentially-novel / verified-novel.
  Never label model output novel without documented literature review; never fabricate references.
