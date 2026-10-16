"""Autonomous runner: executes the same pipeline via provider APIs.

Bounded by budgets + stopping conditions; supports approval gates and resume
from the last completed stage without repeating expensive calls.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from ..agents.base import CrossExaminationAgent, ReconstructionAgent, SolverAgent, VerifierAgent
from ..agents.analogy_generator import draft_analogy_skeleton
from ..core.claims import DialogueTurn, ReconstructionRecord, SolverResponse, VerificationRecord, ClaimRecord
from ..core.experiment import Experiment
from ..core.statuses import AutonomyLevel, ExperimentStage, VerificationStatus
from ..prompts import prompt_version
from ..providers.base import BaseProvider
from ..storage.repository import save_experiment
from .budgets import BudgetState, stopping_reason
from .checkpoints import check_gate
from .manual import CROSS_ROLES


@dataclass
class RunReport:
    stopped: bool = False
    reason: str = ""
    model_calls: int = 0
    stages_completed: list[str] = field(default_factory=list)


def _consume(exp: Experiment, budgets: BudgetState, resp_text: str) -> None:
    # Rough token proxy: ~4 chars/token when usage metadata absent.
    budgets.consume(calls=1, tokens=max(1, len(resp_text) // 4))
    exp.model_calls_made += 1
    exp.tokens_used = budgets.tokens_used


def run_autonomous(
    exp: Experiment,
    provider: BaseProvider,
    *,
    stop_after: str = "audit",
    auto_approve: bool = False,
    model: str = "",
    n_solvers: int = 3,
    root=None,
) -> RunReport:
    level = int(exp.config.autonomy_level.value) if hasattr(exp.config.autonomy_level, "value") else int(exp.config.autonomy_level)
    b = exp.config.budgets
    budgets = BudgetState(max_calls=b.max_model_calls, max_tokens=b.max_tokens,
                          time_limit_s=b.time_limit_s, calls_made=exp.model_calls_made,
                          tokens_used=exp.tokens_used)
    report = RunReport()
    iterations = 0

    def note(stage: str) -> None:
        report.stages_completed.append(stage)

    # --- Stage: analogy generation ---
    if exp.problem is None:
        raise ValueError("Experiment has no problem specification.")
    if not exp.analogies:
        if not check_gate(exp, "accept_analogy", level, auto_approve):
            report.stopped, report.reason = True, "paused at accept_analogy gate"
            save_experiment(exp, root)
            return report
        a = draft_analogy_skeleton(exp, exp.problem)
        # Autonomous fill: ask provider to draft analogy content.
        try:
            from ..agents.base import AnalogyGeneratorAgent
            prompt = AnalogyGeneratorAgent().build_prompt(exp.problem)
            resp = provider.complete(prompt, model=model or exp.config.analogy_model if (model or exp.config.analogy_model) != "researcher" else (model or ""))
            _consume(exp, budgets, resp.text)
            report.model_calls += 1
            a.analogy_statement = resp.text[:4000]
            from ..agents.analogy_generator import refresh_prompts
            refresh_prompts(a, exp.problem)
        except Exception as exc:
            exp.touch("provider_error", {"stage": "analogy", "error": str(exc)[:500]})
        exp.analogies.append(a)
        exp.stage = ExperimentStage.ANALOGY_GENERATED
        exp.touch("analogy_generated", {"analogy_id": a.id, "autonomous": True})
        note("analogy_generated")

    analogy = exp.analogies[0]
    if not analogy.approved:
        if not check_gate(exp, "accept_analogy", level, auto_approve):
            save_experiment(exp, root)
            report.stopped, report.reason = True, "paused at accept_analogy gate"
            return report
        if analogy.leakage and not analogy.leakage.passed:
            exp.touch("leakage_warning", {"findings": [f.model_dump() for f in analogy.leakage.findings]})
        analogy.approve()
        exp.stage = ExperimentStage.ANALOGY_APPROVED
        note("analogy_approved")

    if stop_after in ("analogy",):
        save_experiment(exp, root)
        return report

    # --- Stage: independent solvers (isolated: no peer info in prompts) ---
    solver_agent = SolverAgent()
    needed = max(0, n_solvers - len([r for r in exp.solver_responses if r.analogy_id == analogy.id]))
    for i in range(needed):
        if not check_gate(exp, "extra_calls", level, auto_approve):
            report.stopped, report.reason = True, "paused at extra_calls gate"
            save_experiment(exp, root)
            return report
        if (r := budgets.exhausted()) is not None:
            report.stopped, report.reason = True, r
            save_experiment(exp, root)
            return report
        prompt = solver_agent.build_prompt(analogy)
        solver_label = f"solver-{len(exp.solver_responses) + 1}"
        try:
            resp = provider.complete(prompt, model=model or solver_label)
        except Exception as exc:
            exp.touch("provider_error", {"stage": "solving", "error": str(exc)[:500]})
            save_experiment(exp, root)
            report.stopped, report.reason = True, f"provider error: {exc}"
            return report
        _consume(exp, budgets, resp.text)
        report.model_calls += 1
        sr = SolverResponse(
            id=f"sr-{uuid.uuid4().hex[:8]}", experiment_id=exp.id, analogy_id=analogy.id,
            solver_name=solver_label, model_name=resp.model or solver_label,
            prompt_version=prompt_version("independent_solver"), prompt_text=prompt,
            raw_response=resp.text, disclosed_original=False,
        )
        exp.solver_responses.append(solver_agent.parse(sr))
        exp.touch("solver_response", {"id": sr.id, "solver": solver_label})
    exp.stage = ExperimentStage.SOLVED
    note("solved")
    if stop_after in ("solving", "solved"):
        save_experiment(exp, root)
        return report

    # --- Stage: cross-examination (peer excerpts introduced ONLY here) ---
    if not exp.dialogue:
        peer = exp.solver_responses[0].raw_response[:2000] if exp.solver_responses else ""
        claims = "\n".join(f"- {c}" for r in exp.solver_responses for c in r.candidate_lemmas[:3])
        ce = CrossExaminationAgent()
        for role in ["critic", "counterexample_hunter", "alternative_explorer"]:
            if (r := budgets.exhausted()) is not None:
                report.stopped, report.reason = True, r
                save_experiment(exp, root)
                return report
            prompt = ce.build_prompt(role=role, analogy=analogy, peer_excerpt=peer, claims=claims)
            try:
                resp = provider.complete(prompt, model=model or role)
            except Exception as exc:
                exp.touch("provider_error", {"stage": "cross_exam", "error": str(exc)[:500]})
                break
            _consume(exp, budgets, resp.text)
            report.model_calls += 1
            exp.dialogue.append(DialogueTurn(
                id=f"dt-{uuid.uuid4().hex[:8]}", experiment_id=exp.id, role=role,
                author_model=resp.model or role, prompt_text=prompt, response_text=resp.text))
            iterations += 1
        exp.stage = ExperimentStage.CROSS_EXAM
        note("cross_exam")

    # --- Stage: reconstruction (original revealed; gate recorded) ---
    if not exp.reconstructions:
        if not check_gate(exp, "reveal_original", level, auto_approve):
            save_experiment(exp, root)
            report.stopped, report.reason = True, "paused at reveal_original gate"
            return report
        if (r := budgets.exhausted()) is not None:
            report.stopped, report.reason = True, r
            save_experiment(exp, root)
            return report
        insights = [c for r in exp.solver_responses for c in r.candidate_lemmas[:5]]
        prompt = ReconstructionAgent().build_prompt(
            problem=exp.problem, analogy=analogy,
            solver_summaries="\n".join(f"- {s}" for s in [r.raw_response[:800] for r in exp.solver_responses]),
            dialogue_summaries="\n".join(f"[{t.role}] {t.response_text[:800]}" for t in exp.dialogue),
            selected_insights="\n".join(f"- {s}" for s in insights) or "(none)",
        )
        try:
            resp = provider.complete(prompt, model=model or "reconstructor")
        except Exception as exc:
            exp.touch("provider_error", {"stage": "reconstruction", "error": str(exc)[:500]})
            save_experiment(exp, root)
            report.stopped, report.reason = True, f"provider error: {exc}"
            return report
        _consume(exp, budgets, resp.text)
        report.model_calls += 1
        rec = ReconstructionRecord(id=f"rc-{uuid.uuid4().hex[:8]}", experiment_id=exp.id,
                                   prompt_text=prompt, raw_response=resp.text,
                                   model_name=resp.model or "reconstructor")
        import re as _re
        chunks = _re.split(r"(?im)^\s*(?:-\s*)?CLAIM\s*:", resp.text)[1:]
        if not chunks:
            # Fallback: keep one candidate claim pointing at the raw text so the
            # audit stage always has something to triage (raw stays authoritative).
            cr = ClaimRecord(id=f"cl-{uuid.uuid4().hex[:8]}", experiment_id=exp.id,
                             statement=resp.text.strip()[:2000] or "(empty reconstruction)",
                             analogy_insight="(no explicit CLAIM marker; see raw reconstruction)")
            cr.append_history("autonomous reconstruction (fallback: no CLAIM marker found)")
            rec.claims.append(cr)
        for i, ch in enumerate(chunks, 1):
            cr = ClaimRecord(id=f"cl-{uuid.uuid4().hex[:8]}", experiment_id=exp.id,
                             statement=ch.strip()[:2000])
            cr.append_history("autonomous reconstruction")
            rec.claims.append(cr)
        exp.reconstructions.append(rec)
        exp.stage = ExperimentStage.RECONSTRUCTED
        exp.touch("reconstruction", {"id": rec.id, "claims": len(rec.claims)})
        note("reconstructed")

    # --- Stage: verification triage (model suggests; human must confirm PROVEN) ---
    if stop_after in ("audit", "verify", "report", "all") and exp.reconstructions and not exp.verifications:
        va = VerifierAgent()
        for rec in exp.reconstructions:
            for claim in rec.claims:
                if (r := budgets.exhausted()) is not None:
                    report.stopped, report.reason = True, r
                    save_experiment(exp, root)
                    return report
                prompt = va.build_prompt(
                    claim_statement=claim.statement, claim_assumptions="; ".join(claim.assumptions),
                    derivation=claim.derivation, missing="; ".join(claim.missing_lemmas),
                    problem_statement=exp.problem.statement,
                    obligations="; ".join(exp.problem.proof_obligations),
                    finite_checks="(none run)", known_results="; ".join(exp.problem.known_results))
                try:
                    resp = provider.complete(prompt, model=model or "verifier")
                except Exception:
                    break
                _consume(exp, budgets, resp.text)
                report.model_calls += 1
                suggested = va.suggest_status(resp.text)
                claim.verification = VerificationStatus(suggested)
                claim.verification_notes = (
                    "Autonomous model triage only (NOT final). Human review required. "
                    f"Suggested: {suggested}. Rationale: {resp.text[:500]}"
                )
                exp.verifications.append(VerificationRecord(
                    id=f"vr-{uuid.uuid4().hex[:8]}", experiment_id=exp.id, claim_id=claim.id,
                    status=VerificationStatus(suggested), method="model-triage",
                    notes=claim.verification_notes, reviewer=resp.model or "verifier"))
        exp.stage = ExperimentStage.AUDITED
        note("audited")

    reason = stopping_reason(exp=exp, budgets=budgets, iterations=iterations,
                             max_iterations=b.max_iterations, no_progress_rounds=0)
    if reason:
        report.stopped, report.reason = True, reason
    save_experiment(exp, root)
    return report


def resume_autonomous(exp: Experiment, provider: BaseProvider, **kwargs) -> RunReport:
    """Resume from last completed stage: run_autonomous only fills missing stages."""
    return run_autonomous(exp, provider, **kwargs)
