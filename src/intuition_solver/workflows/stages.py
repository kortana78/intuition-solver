"""Stage helpers: ordered pipeline stages + resume support."""

from __future__ import annotations

from ..core.statuses import ExperimentStage

ORDER = [
    ExperimentStage.CREATED,
    ExperimentStage.SPECIFIED,
    ExperimentStage.ANALOGY_GENERATED,
    ExperimentStage.ANALOGY_APPROVED,
    ExperimentStage.SOLVING,
    ExperimentStage.SOLVED,
    ExperimentStage.CROSS_EXAM,
    ExperimentStage.RECONSTRUCTED,
    ExperimentStage.AUDITED,
    ExperimentStage.REPORTED,
]


def next_stage(current: ExperimentStage) -> ExperimentStage | None:
    try:
        i = ORDER.index(current)
    except ValueError:
        return None
    return ORDER[i + 1] if i + 1 < len(ORDER) else None


def advance_to(current: ExperimentStage, target: ExperimentStage) -> list[ExperimentStage]:
    """Stages between current (exclusive) and target (inclusive) for resume planning."""
    ci, ti = ORDER.index(current), ORDER.index(target)
    if ti <= ci:
        return []
    return ORDER[ci + 1: ti + 1]
