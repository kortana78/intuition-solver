"""Versioned artifacts: every mutation appends an event; exports are stamped."""

from __future__ import annotations

from ..core.experiment import Experiment
from . import repository as _repo


def record_version(exp: Experiment, label: str, root=None) -> str:
    exp.touch("version", {"label": label})
    _repo.save_experiment(exp, root)
    return f"{exp.id}@event-{len(exp.events) - 1} ({label})"
