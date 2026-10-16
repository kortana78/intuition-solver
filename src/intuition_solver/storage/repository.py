"""File-based experiment repository: experiments/<id>/experiment.json + events.jsonl."""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..core.experiment import Experiment

DEFAULT_ROOT = Path(os.environ.get("INTUITION_ROOT", "experiments"))


def _root(root: str | Path | None) -> Path:
    if root is not None:
        return Path(root)
    # Resolve per-call so tests / CLI env overrides (INTUITION_ROOT) take effect.
    return Path(os.environ.get("INTUITION_ROOT", "experiments"))


def experiment_dir(exp_id: str, root: str | Path | None = None) -> Path:
    return _root(root) / exp_id


def save_experiment(exp: Experiment, root: str | Path | None = None) -> Path:
    d = experiment_dir(exp.id, root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "experiment.json").write_text(exp.model_dump_json(indent=2), encoding="utf-8")
    # Append-only event mirror (rewrite is cheap + keeps single source of truth).
    with (d / "events.jsonl").open("w", encoding="utf-8") as fh:
        for ev in exp.events:
            fh.write(ev.model_dump_json() + "\n")
    return d


def load_experiment(exp_id: str, root: str | Path | None = None) -> Experiment:
    p = experiment_dir(exp_id, root) / "experiment.json"
    if not p.exists():
        # also allow passing a path directly
        alt = Path(exp_id) / "experiment.json"
        if alt.exists():
            p = alt
        else:
            raise FileNotFoundError(f"Experiment '{exp_id}' not found in {_root(root)}")
    return Experiment.model_validate_json(p.read_text(encoding="utf-8"))


def list_experiments(root: str | Path | None = None) -> list[str]:
    r = _root(root)
    if not r.exists():
        return []
    return sorted(p.name for p in r.iterdir() if p.is_dir() and (p / "experiment.json").exists())


def export_anonymized(exp: Experiment) -> dict:
    """Strip secrets / API metadata before publication."""
    data = exp.model_dump()
    # Drop anything resembling secrets (defensive: provider keys are never stored, but be safe).
    import re as _re

    text = json.dumps(data)
    text = _re.sub(r"(?i)(api[_-]?key['\"]?\s*[:=]\s*['\"]?)[^'\",\s}]+", r"\1[REDACTED]", text)
    text = _re.sub(r"Bearer\s+[A-Za-z0-9._\-]+", "Bearer [REDACTED]", text)
    return json.loads(text)
