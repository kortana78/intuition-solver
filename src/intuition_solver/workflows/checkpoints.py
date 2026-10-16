"""Checkpoints: approval gates before sensitive/expensive actions."""

from __future__ import annotations

from ..core.experiment import Experiment
from .budgets import needs_approval


def check_gate(exp: Experiment, gate: str, autonomy_level: int, auto_approve: bool = False) -> bool:
    """Return True if the action may proceed. Records the decision as an event."""
    required = needs_approval(gate, exp, autonomy_level)
    approved = auto_approve or not required
    exp.touch("checkpoint", {"gate": gate, "required": required, "approved": approved,
                             "autonomy_level": autonomy_level})
    return approved
