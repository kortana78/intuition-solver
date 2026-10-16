"""Intuition Solver: unified research framework + autonomous multi-agent system."""

__version__ = "0.1.0"

from .core.statuses import (
    AutonomyLevel,
    ConditionKind,
    ExperimentStage,
    VerificationStatus,
    NoveltyStatus,
)

__all__ = [
    "__version__",
    "AutonomyLevel",
    "ConditionKind",
    "ExperimentStage",
    "VerificationStatus",
    "NoveltyStatus",
]
