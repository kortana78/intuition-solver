"""Problem specification data model (Stage 1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ObjectiveTracker(BaseModel):
    """Tracks the original goal vs current subproblem to reduce objective drift."""

    original_goal: str = ""
    current_subproblem: str = ""
    progress_summary: str = ""
    unresolved_obligations: list[str] = Field(default_factory=list)

    def advance(
        self,
        current_subproblem: str = "",
        progress_summary: str = "",
        unresolved: list[str] | None = None,
    ) -> None:
        if current_subproblem:
            self.current_subproblem = current_subproblem
        if progress_summary:
            self.progress_summary = progress_summary
        if unresolved is not None:
            self.unresolved_obligations = list(unresolved)


class ProblemSpecification(BaseModel):
    id: str = Field(default="", description="Stable id, usually exp id + ':problem'")
    title: str = ""
    statement: str = Field(description="Original mathematical problem statement verbatim")
    definitions: list[str] = Field(default_factory=list)
    notation: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list, description="Explicit assumptions")
    desired_theorem: str = ""
    known_results: list[str] = Field(default_factory=list)
    known_references: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    partial_results: list[str] = Field(default_factory=list)
    attempted_approaches: list[str] = Field(default_factory=list)
    research_objective: str = ""
    proof_obligations: list[str] = Field(default_factory=list)
    # Epistemic hygiene: keep facts separate from conjectures/open questions.
    established_facts: list[str] = Field(default_factory=list)
    conjectures: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    tracker: ObjectiveTracker = Field(default_factory=ObjectiveTracker)
    created_at: str = Field(default_factory=_utcnow)
    updated_at: str = Field(default_factory=_utcnow)

    def touch(self) -> None:
        self.updated_at = _utcnow()

    def forbidden_terms(self) -> list[str]:
        """Candidate identifying terms that blind prompts must avoid.

        Heuristic: title words + notation tokens + conjecture names supplied
        by the researcher. Used by the leakage checker; not a guarantee of
        semantic concealment.
        """
        terms: list[str] = []
        for chunk in [self.title, self.desired_theorem, self.research_objective]:
            for w in chunk.replace(",", " ").replace(";", " ").split():
                w = w.strip("().:'\"")
                if len(w) >= 4:
                    terms.append(w)
        for n in self.notation:
            token = n.strip()
            if token:
                # keep short math tokens too (e.g. zeta, pi) for audit purposes
                terms.append(token)
        # de-dup preserving order
        seen: set[str] = set()
        out: list[str] = []
        for t in terms:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                out.append(t)
        return out

    def validate_completeness(self) -> list[str]:
        """Return list of missing-field warnings (does not invent content)."""
        warnings: list[str] = []
        if not self.statement.strip():
            warnings.append("Problem statement is empty.")
        if not self.desired_theorem.strip():
            warnings.append("Desired theorem/conclusion is missing.")
        if not self.proof_obligations:
            warnings.append("No proof obligations listed.")
        if not self.research_objective.strip():
            warnings.append("Research objective is missing.")
        return warnings
