"""Serialization + versioning helpers."""

from __future__ import annotations

from ..core.experiment import Experiment

SCHEMA_VERSION = "1.0"


def to_json(exp: Experiment) -> str:
    return exp.model_dump_json(indent=2)


def from_json(text: str) -> Experiment:
    return Experiment.model_validate_json(text)


def schema_version() -> str:
    return SCHEMA_VERSION
