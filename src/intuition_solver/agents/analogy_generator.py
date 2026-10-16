"""Analogy construction helpers shared by manual + autonomous modes."""

from __future__ import annotations

import uuid

from ..core.analogy import Analogy, CorrespondenceEntry, check_blind_leakage
from ..core.experiment import Experiment
from ..core.problem import ProblemSpecification
from ..prompts import render

ANALOGY_DOMAINS = [
    "networks and graph structures",
    "resource allocation",
    "games and strategic interactions",
    "geometric arrangements",
    "information transmission",
    "dynamical systems",
    "combinatorial constructions",
    "abstract physical systems",
]


def draft_analogy_skeleton(
    exp: Experiment,
    problem: ProblemSpecification,
    domain: str = "networks and graph structures",
    title: str = "",
) -> Analogy:
    """Create an editable analogy skeleton (researcher fills or autonomous model fills)."""
    aid = f"an-{uuid.uuid4().hex[:8]}"
    analogy_statement = (
        f"[DRAFT {domain}] Self-contained analogy goes here. "
        "REPLACE this draft with a fully self-contained problem in the analogy domain, "
        "using fresh vocabulary with no reference to the original field, notation, or title."
    )
    a = Analogy(
        id=aid,
        experiment_id=exp.id,
        domain=domain,
        title=title or f"Analogy 1 ({domain})",
        analogy_statement=analogy_statement,
        objects=["O1: <replace>"],
        relationships=["R1: <replace>"],
        constraints=["C1: <replace>"],
        objective="State what counts as solving the analogy.",
        correspondence=[CorrespondenceEntry(original_element="<orig>", analogy_element="<analog>", preservation="approximate")],
        preserved_properties=["<structural property that must be preserved>"],
        lost_properties=["<property distorted or dropped>"],
        introduced_assumptions=["T1: <assumption added by translation>"],
        invalidating_questions=["Q1: what observation would invalidate this analogy?"],
    )
    a.blind_prompt = build_blind_prompt(a)
    a.audit_prompt = build_audit_prompt(a, problem)
    a.leakage = check_blind_leakage(a.blind_prompt, problem.forbidden_terms())
    return a


def build_blind_prompt(analogy: Analogy) -> str:
    return render(
        "independent_solver",
        ANALOGY_DOMAIN=analogy.domain,
        ANALOGY_STATEMENT=analogy.analogy_statement,
        ANALOGY_OBJECTS="\n".join(analogy.objects),
        ANALOGY_RELATIONSHIPS="\n".join(analogy.relationships),
        ANALOGY_CONSTRAINTS="\n".join(analogy.constraints),
        ANALOGY_OBJECTIVE=analogy.objective,
    )


def build_audit_prompt(analogy: Analogy, problem: ProblemSpecification) -> str:
    from ..core.correspondence import correspondence_table_markdown

    return render(
        "analogy_audit",
        PROBLEM_TITLE=problem.title,
        PROBLEM_STATEMENT=problem.statement,
        FORBIDDEN_TERMS=", ".join(problem.forbidden_terms()[:30]) or "(none)",
        ANALOGY_STATEMENT=f"[{analogy.domain}] {analogy.analogy_statement}",
        CORRESPONDENCE=correspondence_table_markdown(analogy),
        PRESERVED="; ".join(analogy.preserved_properties),
        LOST="; ".join(analogy.lost_properties),
        INTRODUCED_ASSUMPTIONS="; ".join(analogy.introduced_assumptions),
        PROOF_OBLIGATIONS="\n".join(problem.proof_obligations) or "(none)",
        INVALIDATING_QUESTIONS="\n".join(analogy.invalidating_questions),
    )


def refresh_prompts(analogy: Analogy, problem: ProblemSpecification) -> Analogy:
    analogy.blind_prompt = build_blind_prompt(analogy)
    analogy.audit_prompt = build_audit_prompt(analogy, problem)
    analogy.leakage = check_blind_leakage(analogy.blind_prompt, problem.forbidden_terms())
    return analogy
