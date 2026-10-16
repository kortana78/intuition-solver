# Solved-demo README

Offline end-to-end demo (`even + even = even`). All "model" texts are
**clearly labelled illustrative placeholders**, not experimental findings.

Run:

```bash
pip install -e .
python examples/solved_problem/run_demo.py
```

To use real models: replace each file in `illustrative_responses/` with a pasted
response from an external AI tool (manual mode), or configure a provider and run
`intuition run --id demo-even --provider openai_compatible --yes`.
