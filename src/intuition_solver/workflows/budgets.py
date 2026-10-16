"""Budgets, checkpoints, stopping conditions shared by manual + autonomous modes."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..core.experiment import Experiment


@dataclass
class BudgetState:
    max_calls: int = 30
    max_tokens: int = 100_000
    time_limit_s: int = 1800
    calls_made: int = 0
    tokens_used: int = 0
    started_at: float = field(default_factory=time.time)

    def exhausted(self) -> str | None:
        if self.calls_made >= self.max_calls:
            return f"model-call budget exhausted ({self.calls_made}/{self.max_calls})"
        if self.tokens_used >= self.max_tokens:
            return f"token budget exhausted ({self.tokens_used}/{self.max_tokens})"
        if (time.time() - self.started_at) >= self.time_limit_s:
            return f"time limit reached ({self.time_limit_s}s)"
        return None

    def consume(self, calls: int = 1, tokens: int = 0) -> None:
        self.calls_made += calls
        self.tokens_used += tokens


REQUIRED_CHECKPOINTS = ["reveal_original", "accept_analogy", "extra_calls", "overspend"]


def needs_approval(checkpoint: str, exp: Experiment, autonomy_level: int) -> bool:
    """Level 0/1 always require approval; Level 2 pauses at configured checkpoints;
    Level 3 only pauses at overspend/reveal unless configured otherwise."""
    cps = exp.config.checkpoints or []
    if autonomy_level <= 1:
        return True
    if autonomy_level == 2:
        return checkpoint in cps
    # Level 3
    return checkpoint in ("overspend", "reveal_original") and checkpoint in cps


def stopping_reason(
    *,
    exp: Experiment,
    budgets: BudgetState,
    iterations: int,
    max_iterations: int,
    no_progress_rounds: int,
    cancelled: bool = False,
    candidate_proof: bool = False,
    counterexample_found: bool = False,
    critical_gap: bool = False,
) -> str | None:
    if cancelled:
        return "researcher paused or cancelled"
    if (r := budgets.exhausted()) is not None:
        return r
    if iterations >= max_iterations:
        return f"iteration limit reached ({iterations}/{max_iterations})"
    if no_progress_rounds >= exp.config.budgets.no_progress_rounds and iterations > 0:
        return f"no useful progress over {no_progress_rounds} rounds"
    if candidate_proof:
        return "candidate proof produced; human review required (verification, not success)"
    if counterexample_found:
        return "counterexample invalidates current conjecture; stopping for review"
    if critical_gap:
        return "verifier identified a critical unresolved gap; stopping for review"
    return None
