# Manual mode (no API key)

1. `intuition init --title "My problem" --id myexp --statement "..."` (or `--problem-file`).
2. `intuition show --id myexp`: check missing stages.
3. `intuition generate-analogy --id myexp --domain "resource allocation"`.
4. Edit `experiments/myexp/experiment.json`: fill `analogy_statement`, objects, correspondence, preservation.
5. `intuition approve-analogy --id myexp --analogy <an-id>` (after auditing leakage).
6. `intuition export-prompts --id myexp --analogy <an-id>`: copy each `solver-N_blind.md` into a **separate** external model; do not reveal the original.
7. Save each answer to a file; `intuition import-response --id myexp --analogy <an-id> --solver solver-N --file ansN.md --model "ModelName vX"`.
8. `intuition cross-examine --id myexp --analogy <an-id> --role critic --file reply.md` (repeat per role).
9. `intuition reconstruct --id myexp --analogy <an-id> --file recon.md --insight "..."` (print prompt with `--print-prompt`).
10. `intuition audit --id myexp --set <claim>=CONJECTURE --note <claim>="human: reason"` (PROVEN needs a `human:`/`lean` note).
11. `intuition report --id myexp` / `intuition export --id myexp`.

Web review: `uvicorn intuition_solver.web.app:app --reload`, then open http://127.0.0.1:8000.
Never paste secrets into responses; exports are anonymized.
