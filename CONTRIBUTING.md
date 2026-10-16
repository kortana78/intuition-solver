# Contributing

- Python 3.11 or newer; `pip install -e ".[dev]"`; run `pytest -q` before PRs.
- Manual mode must keep working with **no API key**; never hardcode a provider.
- Append-only records: never overwrite raw prompts/responses; add events, don't rewrite history.
- A model alone never confers PROVEN; enforce human/Lean sign-off.
- No fabricated results, references, or "novel discovery" claims without documented evidence.
- Mock/illustrative outputs must stay labelled as such.
