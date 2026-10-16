"""Analogy + correspondence-map data models (Stage 2)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class CorrespondenceEntry(BaseModel):
    original_element: str = ""
    analogy_element: str = ""
    preservation: str = "preserved"  # preserved | approximate | lost
    notes: str = ""


class LeakageFinding(BaseModel):
    term: str
    context: str = ""  # short snippet where it appears


class LeakageReport(BaseModel):
    passed: bool = True
    findings: list[LeakageFinding] = Field(default_factory=list)
    checked_at: str = Field(default_factory=_utcnow)
    note: str = (
        "Automated checks are heuristic string matches; they cannot guarantee "
        "complete semantic concealment. Researcher audit is required."
    )


class Analogy(BaseModel):
    id: str = ""
    experiment_id: str = ""
    domain: str = ""  # e.g. networks, resource allocation, games, ...
    title: str = ""
    # Self-contained analogy description
    analogy_statement: str = ""
    objects: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    objective: str = ""
    correspondence: list[CorrespondenceEntry] = Field(default_factory=list)
    preserved_properties: list[str] = Field(default_factory=list)
    lost_properties: list[str] = Field(default_factory=list)
    introduced_assumptions: list[str] = Field(default_factory=list)
    invalidating_questions: list[str] = Field(default_factory=list)
    # Prompts
    blind_prompt: str = ""
    audit_prompt: str = ""
    leakage: Optional[LeakageReport] = None
    approved: bool = False
    approved_at: Optional[str] = None
    created_at: str = Field(default_factory=_utcnow)

    def approve(self) -> None:
        self.approved = True
        self.approved_at = _utcnow()


def check_blind_leakage(blind_prompt: str, forbidden_terms: list[str]) -> LeakageReport:
    """Heuristic case-insensitive substring check for identity leakage."""
    lowered = blind_prompt.lower()
    findings: list[LeakageFinding] = []
    for term in forbidden_terms:
        t = term.strip()
        if len(t) < 4:
            continue
        tl = t.lower()
        if tl and tl in lowered:
            idx = lowered.index(tl)
            start = max(0, idx - 40)
            end = min(len(blind_prompt), idx + len(t) + 40)
            findings.append(LeakageFinding(term=t, context=blind_prompt[start:end]))
    return LeakageReport(passed=not findings, findings=findings)
