"""Agent layer: thin wrappers that build prompts and parse Section-style outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..core.analogy import Analogy, check_blind_leakage
from ..core.claims import DialogueTurn, SolverResponse
from ..core.problem import ProblemSpecification
from ..prompts import prompt_version, render


def _section(text: str, name: str) -> str:
    m = re.search(rf"(?ims)^\s*(?:\d+\.\s*)?{re.escape(name)}\s*:(.*?)(?=^\s*(?:\d+\.\s*)?[A-Z_]{{3,}}\s*:|\Z)", text)
    return m.group(1).strip() if m else ""


def _bullets(text: str) -> list[str]:
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("-", "*", "+")):
            out.append(s[1:].strip())
        elif re.match(r"^[A-Z0-9]+[.)]\s+\S", s):
            out.append(re.sub(r"^[A-Z0-9]+[.)]\s+", "", s).strip())
    return [x for x in out if x]


@dataclass
class AgentResult:
    prompt: str
    response: str


class BaseAgent:
    role = "base"

    def build_prompt(self, **kwargs) -> str:
        raise NotImplementedError


class AnalogyGeneratorAgent(BaseAgent):
    role = "analogy_generator"

    def build_prompt(self, problem: ProblemSpecification) -> str:
        return render(
            "analogy_generation",
            PROBLEM_TITLE=problem.title,
            PROBLEM_STATEMENT=problem.statement,
            DEFINITIONS="\n".join(problem.definitions) or "(none supplied)",
            ASSUMPTIONS="\n".join(problem.assumptions) or "(none)",
            DESIRED_THEOREM=problem.desired_theorem or "(none)",
            PROOF_OBLIGATIONS="\n".join(problem.proof_obligations) or "(none)",
        )


class SolverAgent(BaseAgent):
    role = "solver"

    def build_prompt(self, analogy: Analogy) -> str:
        return render(
            "independent_solver",
            ANALOGY_DOMAIN=analogy.domain,
            ANALOGY_STATEMENT=analogy.analogy_statement,
            ANALOGY_OBJECTS="\n".join(analogy.objects) or "(see statement)",
            ANALOGY_RELATIONSHIPS="\n".join(analogy.relationships) or "(see statement)",
            ANALOGY_CONSTRAINTS="\n".join(analogy.constraints) or "(see statement)",
            ANALOGY_OBJECTIVE=analogy.objective,
        )

    def parse(self, resp: SolverResponse) -> SolverResponse:
        t = resp.raw_response
        resp.interpretation = _section(t, "INTERPRETATION")
        resp.proposed_solution = _section(t, "PROPOSED_SOLUTION")
        lemmas = _section(t, "CANDIDATE_LEMMAS") or _section(t, "CANDIDATE_LEMMAS".replace("_", " "))
        resp.candidate_lemmas = _bullets(lemmas) or ([lemmas] if lemmas else [])
        resp.reasoning = _section(t, "REASONING")
        resp.assumptions = _bullets(_section(t, "REASONING")) or _bullets(t)
        resp.alternatives = _bullets(_section(t, "ALTERNATIVES")) or ([_section(t, "ALTERNATIVES")] if _section(t, "ALTERNATIVES") else [])
        resp.counterexamples = _bullets(_section(t, "COUNTEREXAMPLES")) or ([_section(t, "COUNTEREXAMPLES")] if _section(t, "COUNTEREXAMPLES") else [])
        resp.unresolved = _bullets(_section(t, "UNRESOLVED")) or ([_section(t, "UNRESOLVED")] if _section(t, "UNRESOLVED") else [])
        resp.confidence = _section(t, "CONFIDENCE")
        resp.proof_status_claim = _section(t, "PROOF_STATUS")
        return resp


class CrossExaminationAgent(BaseAgent):
    role = "cross_examination"

    def build_prompt(self, *, role: str, analogy: Analogy, peer_excerpt: str, claims: str) -> str:
        return render(
            "cross_examination",
            ROLE=role,
            ANALOGY_STATEMENT=analogy.analogy_statement,
            ANALOGY_OBJECTIVE=analogy.objective,
            PEER_EXCERPT=peer_excerpt,
            CLAIMS_UNDER_REVIEW=claims,
        )


class ReconstructionAgent(BaseAgent):
    role = "reconstructor"

    def build_prompt(
        self,
        *,
        problem: ProblemSpecification,
        analogy: Analogy,
        solver_summaries: str,
        dialogue_summaries: str,
        selected_insights: str,
    ) -> str:
        from ..core.correspondence import correspondence_table_markdown

        return render(
            "reconstruction",
            PROBLEM_TITLE=problem.title,
            PROBLEM_STATEMENT=problem.statement,
            DEFINITIONS="\n".join(problem.definitions) or "(none)",
            ASSUMPTIONS="\n".join(problem.assumptions) or "(none)",
            DESIRED_THEOREM=problem.desired_theorem or "(none)",
            PROOF_OBLIGATIONS="\n".join(problem.proof_obligations) or "(none)",
            ANALOGY_DOMAIN=analogy.domain,
            ANALOGY_STATEMENT=analogy.analogy_statement,
            CORRESPONDENCE=correspondence_table_markdown(analogy),
            PRESERVED="; ".join(analogy.preserved_properties) or "(none)",
            LOST="; ".join(analogy.lost_properties) or "(none)",
            INTRODUCED_ASSUMPTIONS="; ".join(analogy.introduced_assumptions) or "(none)",
            SOLVER_SUMMARIES=solver_summaries,
            DIALOGUE_SUMMARIES=dialogue_summaries,
            SELECTED_INSIGHTS=selected_insights,
        )


class VerifierAgent(BaseAgent):
    """Triage only: proposes a suggested status. Final PROVEN requires human/Lean sign-off."""

    role = "verifier"

    def build_prompt(self, *, claim_statement: str, claim_assumptions: str, derivation: str,
                     missing: str, problem_statement: str, obligations: str,
                     finite_checks: str, known_results: str) -> str:
        return render(
            "proof_audit",
            CLAIM_STATEMENT=claim_statement,
            CLAIM_ASSUMPTIONS=claim_assumptions,
            CLAIM_DERIVATION=derivation,
            MISSING_LEMMAS=missing,
            PROBLEM_STATEMENT=problem_statement,
            PROOF_OBLIGATIONS=obligations,
            FINITE_CHECKS=finite_checks,
            KNOWN_RESULTS=known_results,
        )

    def suggest_status(self, audit_text: str) -> str:
        up = audit_text.upper()
        for status in ["REFUTED", "GAP", "CONJECTURE", "COMPUTATIONALLY_SUPPORTED",
                       "KNOWN_RESULT", "PROVEN", "UNVERIFIED"]:
            if status in up:
                # A model alone can never confer PROVEN. Downgrade to UNVERIFIED with note.
                if status == "PROVEN":
                    return "UNVERIFIED"
                return status
        return "UNVERIFIED"
