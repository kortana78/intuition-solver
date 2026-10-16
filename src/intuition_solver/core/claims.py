"""Claims, solver responses, dialogue records, reconstructions, audits (Stages 3-6)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from .statuses import NoveltyStatus, VerificationStatus


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SolverResponse(BaseModel):
    id: str = ""
    experiment_id: str = ""
    analogy_id: str = ""
    solver_name: str = ""  # e.g. solver-1 / model label
    model_name: str = ""
    model_version: str = ""
    prompt_version: str = ""
    prompt_text: str = ""
    raw_response: str = ""
    # Parsed (best-effort) sections; raw_response is authoritative.
    interpretation: str = ""
    proposed_solution: str = ""
    candidate_lemmas: list[str] = Field(default_factory=list)
    reasoning: str = ""
    assumptions: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    counterexamples: list[str] = Field(default_factory=list)
    unresolved: list[str] = Field(default_factory=list)
    confidence: str = ""
    proof_status_claim: str = ""
    disclosed_original: bool = False  # must be False for blind solvers
    imported_at: str = Field(default_factory=_utcnow)


class DialogueTurn(BaseModel):
    id: str = ""
    experiment_id: str = ""
    role: str = ""  # critic | counterexample_hunter | alternative_explorer | synthesizer | controller
    author_model: str = ""
    prompt_text: str = ""
    response_text: str = ""
    addresses_claim_ids: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=_utcnow)


class ClaimRecord(BaseModel):
    """A candidate mathematical insight with full audit trail."""

    id: str = ""
    experiment_id: str = ""
    statement: str = ""
    assumptions: list[str] = Field(default_factory=list)
    analogy_insight: str = ""
    source_analogy_id: str = ""
    source_response_ids: list[str] = Field(default_factory=list)
    derivation: str = ""
    analogy_justifies_inference: str = "unknown"  # yes | no | unknown + rationale
    missing_lemmas: list[str] = Field(default_factory=list)
    proof_obligations: list[str] = Field(default_factory=list)
    counterexamples: list[str] = Field(default_factory=list)
    verification: VerificationStatus = VerificationStatus.UNVERIFIED
    verification_notes: str = ""
    novelty: NoveltyStatus = NoveltyStatus.NOT_CHECKED
    novelty_notes: str = ""
    history: list[str] = Field(default_factory=list, description="Append-only claim evolution notes")
    selected_for_reconstruction: bool = False
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)

    def append_history(self, note: str) -> None:
        self.history.append(f"{_utcnow()} :: {note}")
        self.updated_at = _utcnow()


class FiniteCheck(BaseModel):
    name: str = ""
    code: str = ""
    passed: bool = False
    output: str = ""
    ran_at: str = Field(default_factory=_utcnow)


class VerificationRecord(BaseModel):
    id: str = ""
    experiment_id: str = ""
    claim_id: str = ""
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    method: str = ""  # human | finite-case | symbolic | lean | independent-review | model-triage
    notes: str = ""
    finite_checks: list[FiniteCheck] = Field(default_factory=list)
    reviewer: str = ""
    created_at: str = Field(default_factory=_utcnow)


class ReconstructionRecord(BaseModel):
    id: str = ""
    experiment_id: str = ""
    prompt_text: str = ""
    raw_response: str = ""
    claims: list[ClaimRecord] = Field(default_factory=list)
    rejected_ideas: list[str] = Field(default_factory=list)
    model_name: str = ""
    created_at: str = Field(default_factory=_utcnow)


class ExperimentEvent(BaseModel):
    seq: int = 0
    type: str = ""
    at: str = Field(default_factory=_utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)
