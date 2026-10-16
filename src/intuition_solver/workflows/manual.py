"""Manual workflow: researcher-operated, no API key required.

Every function mutates the Experiment, appends an event, and persists via the
repository. Raw prompts/responses are preserved verbatim; edited summaries are
stored separately and never overwrite raw records.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from ..agents.analogy_generator import build_audit_prompt, build_blind_prompt, draft_analogy_skeleton
from ..agents.base import CrossExaminationAgent, ReconstructionAgent, SolverAgent, VerifierAgent
from ..core.analogy import Analogy, check_blind_leakage
from ..core.claims import DialogueTurn, ReconstructionRecord, SolverResponse, VerificationRecord, ClaimRecord
from ..core.experiment import Experiment
from ..core.problem import ProblemSpecification
from ..core.statuses import ExperimentStage, VerificationStatus
from ..prompts import prompt_version
from ..storage.repository import save_experiment

CROSS_ROLES = ["critic", "counterexample_hunter", "alternative_explorer", "synthesizer", "research_controller"]


def create_experiment(exp_id: str, title: str, research_question: str = "", root=None) -> Experiment:
    exp = Experiment(id=exp_id, title=title, research_question=research_question)
    exp.touch("created", {"title": title})
    save_experiment(exp, root)
    return exp


def set_problem(exp: Experiment, problem: ProblemSpecification, root=None) -> Experiment:
    problem.id = f"{exp.id}:problem"
    if not problem.title:
        problem.title = exp.title
    if not problem.tracker.original_goal:
        problem.tracker.original_goal = problem.research_objective or problem.desired_theorem
    exp.problem = problem
    exp.stage = ExperimentStage.SPECIFIED
    exp.touch("problem_specified", {"warnings": problem.validate_completeness()})
    save_experiment(exp, root)
    return exp


def generate_analogy(exp: Experiment, domain: str = "networks and graph structures",
                     title: str = "", root=None) -> Analogy:
    if exp.problem is None:
        raise ValueError("Specify the problem first (set_problem).")
    a = draft_analogy_skeleton(exp, exp.problem, domain=domain, title=title)
    exp.analogies.append(a)
    exp.stage = ExperimentStage.ANALOGY_GENERATED
    exp.touch("analogy_generated", {"analogy_id": a.id, "domain": domain})
    save_experiment(exp, root)
    return a


def approve_analogy(exp: Experiment, analogy_id: str, root=None) -> Analogy:
    a = exp.get_analogy(analogy_id)
    a.approve()
    exp.stage = ExperimentStage.ANALOGY_APPROVED
    exp.touch("analogy_approved", {"analogy_id": a.id})
    save_experiment(exp, root)
    return a


def export_solver_prompts(exp: Experiment, analogy_id: str, n: int = 3, root=None) -> list[dict]:
    """Return n independent blind prompts (identical text, distinct prompt ids)."""
    a = exp.get_analogy(analogy_id)
    if not a.approved:
        raise ValueError("Approve the analogy before exporting solver prompts.")
    out = []
    for i in range(n):
        out.append({
            "solver": f"solver-{i + 1}",
            "analogy_id": a.id,
            "prompt_version": prompt_version("independent_solver"),
            "blind_prompt": a.blind_prompt,
            "leakage_passed": bool(a.leakage and a.leakage.passed),
        })
    exp.touch("prompts_exported", {"analogy_id": a.id, "n": n})
    save_experiment(exp, root)
    return out


def import_solver_response(
    exp: Experiment,
    analogy_id: str,
    solver: str,
    response_text: str,
    model_name: str = "external-manual",
    model_version: str = "",
    from_file: str = "",
    root=None,
) -> SolverResponse:
    a = exp.get_analogy(analogy_id)
    text = response_text
    if from_file:
        text = Path(from_file).read_text(encoding="utf-8")
    sr = SolverResponse(
        id=f"sr-{uuid.uuid4().hex[:8]}",
        experiment_id=exp.id,
        analogy_id=a.id,
        solver_name=solver,
        model_name=model_name,
        model_version=model_version,
        prompt_version=prompt_version("independent_solver"),
        prompt_text=a.blind_prompt,
        raw_response=text,
        disclosed_original=False,
    )
    sr = SolverAgent().parse(sr)
    exp.solver_responses.append(sr)  # append-only: never overwrite earlier records
    if len(exp.solver_responses) >= 1 and exp.stage.value in ("created", "specified", "analogy_generated", "analogy_approved"):
        exp.stage = ExperimentStage.SOLVING
    if len(exp.solver_responses) >= 3:
        exp.stage = ExperimentStage.SOLVED
    exp.touch("solver_response_imported", {"id": sr.id, "solver": solver, "analogy_id": a.id})
    save_experiment(exp, root)
    return sr


def cross_examine_prompts(exp: Experiment, analogy_id: str, roles: list[str] | None = None, root=None) -> list[dict]:
    roles = roles or ["critic", "counterexample_hunter", "alternative_explorer"]
    a = exp.get_analogy(analogy_id)
    peer = exp.solver_responses[0].raw_response[:2000] if exp.solver_responses else "(no responses yet)"
    claims = "\n".join(f"- {c}" for r in exp.solver_responses for c in r.candidate_lemmas[:3]) or "(no lemmas yet)"
    agent = CrossExaminationAgent()
    out = []
    for role in roles:
        if role not in CROSS_ROLES:
            raise ValueError(f"Unknown cross-examination role '{role}'. Choose from {CROSS_ROLES}")
        out.append({"role": role, "prompt": agent.build_prompt(
            role=role, analogy=a, peer_excerpt=peer, claims=claims)})
    exp.touch("cross_exam_prompts", {"analogy_id": a.id, "roles": roles})
    save_experiment(exp, root)
    return out


def import_dialogue_turn(
    exp: Experiment, role: str, response_text: str, author_model: str = "external-manual",
    addresses: list[str] | None = None, from_file: str = "", root=None,
) -> DialogueTurn:
    text = Path(from_file).read_text(encoding="utf-8") if from_file else response_text
    turn = DialogueTurn(
        id=f"dt-{uuid.uuid4().hex[:8]}", experiment_id=exp.id, role=role,
        author_model=author_model, response_text=text,
        addresses_claim_ids=addresses or [],
    )
    exp.dialogue.append(turn)
    exp.stage = ExperimentStage.CROSS_EXAM
    exp.touch("dialogue_imported", {"id": turn.id, "role": role})
    save_experiment(exp, root)
    return turn


def reconstruction_prompt(exp: Experiment, analogy_id: str, selected_insights: list[str]) -> str:
    if exp.problem is None:
        raise ValueError("No problem specification.")
    a = exp.get_analogy(analogy_id)
    solver_summaries = "\n\n".join(
        f"[{r.solver_name} :: {r.model_name}] {r.raw_response[:1500]}" for r in exp.solver_responses
    ) or "(none)"
    dialogue_summaries = "\n\n".join(
        f"[{t.role} :: {t.author_model}] {t.response_text[:1500]}" for t in exp.dialogue
    ) or "(none)"
    return ReconstructionAgent().build_prompt(
        problem=exp.problem, analogy=a, solver_summaries=solver_summaries,
        dialogue_summaries=dialogue_summaries,
        selected_insights="\n".join(f"- {s}" for s in selected_insights) or "(researcher: list insights)",
    )


def import_reconstruction(exp: Experiment, prompt_text: str, response_text: str,
                          model_name: str = "external-manual", from_file: str = "",
                          root=None) -> ReconstructionRecord:
    text = Path(from_file).read_text(encoding="utf-8") if from_file else response_text
    rec = ReconstructionRecord(
        id=f"rc-{uuid.uuid4().hex[:8]}", experiment_id=exp.id,
        prompt_text=prompt_text, raw_response=text, model_name=model_name,
    )
    # Best-effort claim extraction: split on CLAIM: markers; raw text stays authoritative.
    import re as _re
    chunks = _re.split(r"(?im)^\s*(?:-\s*)?CLAIM\s*:", text)[1:]
    if not chunks:
        cr = ClaimRecord(id=f"cl-{uuid.uuid4().hex[:8]}", experiment_id=exp.id,
                         statement=text.strip()[:2000] or "(empty reconstruction)",
                         analogy_insight="(no explicit CLAIM marker; see raw reconstruction)")
        cr.append_history(f"extracted from reconstruction {rec.id} (fallback)")
        rec.claims.append(cr)
    for i, ch in enumerate(chunks, 1):
        cr = ClaimRecord(id=f"cl-{uuid.uuid4().hex[:8]}", experiment_id=exp.id,
                         statement=ch.strip()[:2000], analogy_insight="(see reconstruction raw)",
                         verification=VerificationStatus.UNVERIFIED)
        cr.append_history(f"extracted from reconstruction {rec.id} chunk {i}")
        rec.claims.append(cr)
    exp.reconstructions.append(rec)
    exp.stage = ExperimentStage.RECONSTRUCTED
    exp.touch("reconstruction_imported", {"id": rec.id, "claims": len(rec.claims)})
    save_experiment(exp, root)
    return rec


def audit_claims(
    exp: Experiment,
    decisions: dict[str, str] | None = None,
    notes: dict[str, str] | None = None,
    finite_results: dict[str, str] | None = None,
    root=None,
) -> list[VerificationRecord]:
    """Human-led audit: researcher assigns final status per claim. Model triage is advisory only."""
    decisions = decisions or {}
    notes = notes or {}
    out: list[VerificationRecord] = []
    for rec in exp.reconstructions:
        for claim in rec.claims:
            status_raw = decisions.get(claim.id, claim.verification.value)
            try:
                status = VerificationStatus(status_raw)
            except ValueError:
                raise ValueError(f"Invalid verification status '{status_raw}' for claim {claim.id}")
            if status == VerificationStatus.PROVEN and "human:" not in (notes.get(claim.id, "") + claim.verification_notes).lower() \
                    and "lean" not in (notes.get(claim.id, "") + claim.verification_notes).lower():
                # Require explicit human or Lean sign-off note for PROVEN.
                raise ValueError(
                    f"Claim {claim.id}: PROVEN requires a human sign-off or Lean check note "
                    "(record reviewer + method). See docs/verification.md."
                )
            claim.verification = status
            if claim.id in notes:
                claim.verification_notes = notes[claim.id]
                claim.append_history(f"audit note: {notes[claim.id][:500]}")
            vr = VerificationRecord(
                id=f"vr-{uuid.uuid4().hex[:8]}", experiment_id=exp.id, claim_id=claim.id,
                status=status, method="human",
                notes=notes.get(claim.id, "") + (f" | finite: {finite_results.get(claim.id, '')}" if finite_results and claim.id in finite_results else ""),
                reviewer="researcher",
            )
            exp.verifications.append(vr)
            out.append(vr)
    exp.stage = ExperimentStage.AUDITED
    exp.touch("audit_completed", {"records": len(out)})
    save_experiment(exp, root)
    return out


def add_note(exp: Experiment, note: str, root=None) -> None:
    exp.researcher_notes.append(note)
    exp.touch("note", {"note": note[:500]})
    save_experiment(exp, root)
