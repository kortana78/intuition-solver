"""Experiment aggregate + correspondence helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from .analogy import Analogy
from .claims import (
    ClaimRecord,
    DialogueTurn,
    ExperimentEvent,
    ReconstructionRecord,
    SolverResponse,
    VerificationRecord,
)
from .problem import ProblemSpecification
from .statuses import AutonomyLevel, ConditionKind, ExperimentStage


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class BudgetConfig(BaseModel):
    max_iterations: int = 5
    max_model_calls: int = 30
    max_tokens: int = 100_000
    time_limit_s: int = 1800
    no_progress_rounds: int = 2


class ExperimentConfig(BaseModel):
    autonomy_level: AutonomyLevel = AutonomyLevel.MANUAL
    condition: ConditionKind = ConditionKind.FULL_ARCHITECTURE
    solver_models: list[str] = Field(default_factory=lambda: ["solver-1", "solver-2", "solver-3"])
    analogy_model: str = "researcher"
    reconstructor_model: str = "researcher"
    budgets: BudgetConfig = Field(default_factory=BudgetConfig)
    checkpoints: list[str] = Field(
        default_factory=lambda: ["reveal_original", "accept_analogy", "extra_calls", "overspend"]
    )
    provider: str = "mock"


class Experiment(BaseModel):
    id: str = ""
    title: str = ""
    research_question: str = ""
    config: ExperimentConfig = Field(default_factory=ExperimentConfig)
    stage: ExperimentStage = ExperimentStage.CREATED
    problem: Optional[ProblemSpecification] = None
    analogies: list[Analogy] = Field(default_factory=list)
    solver_responses: list[SolverResponse] = Field(default_factory=list)
    dialogue: list[DialogueTurn] = Field(default_factory=list)
    reconstructions: list[ReconstructionRecord] = Field(default_factory=list)
    verifications: list[VerificationRecord] = Field(default_factory=list)
    # Baseline records for conditions A-D (free-form but structured)
    baselines: dict[str, Any] = Field(default_factory=dict)
    researcher_notes: list[str] = Field(default_factory=list)
    events: list[ExperimentEvent] = Field(default_factory=list)
    model_calls_made: int = 0
    tokens_used: int = 0
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)

    def touch(self, event_type: str = "", payload: dict[str, Any] | None = None) -> ExperimentEvent:
        self.updated_at = _utcnow()
        ev = ExperimentEvent(seq=len(self.events), type=event_type, payload=payload or {})
        self.events.append(ev)
        return ev

    def get_analogy(self, analogy_id: str) -> Analogy:
        for a in self.analogies:
            if a.id == analogy_id or analogy_id in (a.title,):
                return a
        raise KeyError(f"Analogy '{analogy_id}' not found")

    def incomplete_stages(self) -> list[str]:
        out: list[str] = []
        if self.problem is None:
            out.append("problem specification missing")
        if not self.analogies:
            out.append("no analogies generated")
        elif not any(a.approved for a in self.analogies):
            out.append("no analogy approved")
        if len(self.solver_responses) < 3:
            out.append(f"only {len(self.solver_responses)}/3+ solver responses imported")
        if not self.dialogue:
            out.append("no cross-examination recorded")
        if not self.reconstructions:
            out.append("no reconstruction recorded")
        if not self.verifications:
            out.append("no verification records (claims UNVERIFIED)")
        return out

    def unverified_claims(self) -> list[ClaimRecord]:
        claims: list[ClaimRecord] = []
        for r in self.reconstructions:
            claims.extend(r.claims)
        return [c for c in claims if c.verification.value == "UNVERIFIED"]
