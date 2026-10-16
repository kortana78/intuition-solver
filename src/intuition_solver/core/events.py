"""Append-only event helpers."""

from __future__ import annotations

from typing import Any

from .claims import ExperimentEvent
from .experiment import Experiment


def record(exp: Experiment, event_type: str, payload: dict[str, Any] | None = None) -> ExperimentEvent:
    return exp.touch(event_type, payload or {})
