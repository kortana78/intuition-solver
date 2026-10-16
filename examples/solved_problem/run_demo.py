"""Solved demo: even + even = even, fully offline with mock/illustrative responses.

Run: python examples/solved_problem/run_demo.py
Uses clearly labelled illustrative responses (NOT genuine findings).
"""

from __future__ import annotations

import shutil
from pathlib import Path

from intuition_solver.core.problem import ProblemSpecification
from intuition_solver.evaluation.reports import write_reports
from intuition_solver.providers.mock import MockProvider
from intuition_solver.workflows import manual as M
from intuition_solver.workflows.autonomous import run_autonomous
from intuition_solver.core.experiment import Experiment

ROOT = Path(__file__).parent / "_workspace"
ILLUSTRATIVE = Path(__file__).parent / "illustrative_responses"


def manual_demo() -> str:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    ROOT.mkdir(parents=True)
    exp = M.create_experiment("demo-even", "Even + even = even (solved demo)",
                              "Does analogy-mediated reasoning produce a useful lemma?", root=ROOT)
    M.set_problem(exp, ProblemSpecification(
        title="Even plus even",
        statement="Prove that the sum of two even integers is even.",
        definitions=["An integer n is even iff there exists integer k with n = 2k."],
        notation=["n, m, k"],
        assumptions=["Standard integer arithmetic."],
        desired_theorem="For all even n, m: n + m is even.",
        known_results=["Standard parity facts (undergraduate number theory)."],
        constraints=["Elementary proof only."],
        proof_obligations=["P1: exhibit k with n+m = 2k."],
        established_facts=["2a+2b = 2(a+b)."],
        research_objective="Demonstrate the full lifecycle offline.",
    ), root=ROOT)
    a = M.generate_analogy(exp, domain="resource allocation",
                           title="Paired crates (resource allocation)", root=ROOT)
    # Researcher edits the draft into a genuinely self-contained analogy:
    a.analogy_statement = (
        "A depot stores crates only in sealed pairs. Two shipments arrive, each consisting "
        "solely of sealed pairs. The depot merges them onto one pallet. Can the merged pallet "
        "be re-packed entirely into sealed pairs with nothing left over?"
    )
    a.objects = ["pairs (sealed crates)", "shipments A and B", "merged pallet"]
    a.relationships = ["each shipment is a multiset of pairs", "merge = multiset union"]
    a.constraints = ["no crate may be split; pairs are indivisible units of 2"]
    a.objective = "Decide whether the merged pallet always re-packs into pairs; exhibit the re-packing."
    from intuition_solver.core.analogy import CorrespondenceEntry
    from intuition_solver.agents.analogy_generator import refresh_prompts
    a.correspondence = [
        CorrespondenceEntry(original_element="even integer n=2k", analogy_element="shipment of k pairs",
                            preservation="preserved", notes="k pairs <-> 2k crates"),
        CorrespondenceEntry(original_element="sum n+m", analogy_element="merged pallet",
                            preservation="preserved", notes="addition <-> multiset union"),
    ]
    a.preserved_properties = ["additivity of pairing structure"]
    a.lost_properties = ["sign, primality, order (irrelevant here)"]
    a.introduced_assumptions = ["T1: crates are indistinguishable (matches integer addition commutativity)"]
    a.invalidating_questions = ["Q1: does any shipment contain an unpaired crate? (would break correspondence)"]
    refresh_prompts(a, exp.problem)
    from intuition_solver.storage.repository import save_experiment
    save_experiment(exp, ROOT)
    M.approve_analogy(exp, a.id, root=ROOT)

    for f in sorted(ILLUSTRATIVE.glob("solver-*.md")):
        M.import_solver_response(exp, a.id, f.stem, "", model_name=f"illustrative-{f.stem}",
                                 from_file=str(f), root=ROOT)
    for role, f in [("critic", "cross_critic.md"), ("counterexample_hunter", "cross_counterexample.md")]:
        p = ILLUSTRATIVE / f
        if p.exists():
            M.import_dialogue_turn(exp, role, "", author_model=f"illustrative-{role}",
                                   from_file=str(p), root=ROOT)
    prompt = M.reconstruction_prompt(exp, a.id, ["pairs merge into pairs: k pairs + l pairs = (k+l) pairs"])
    M.import_reconstruction(exp, prompt, "", model_name="illustrative-reconstructor",
                            from_file=str(ILLUSTRATIVE / "reconstruction.md"), root=ROOT)
    claim = exp.reconstructions[0].claims[0]
    M.audit_claims(exp, {claim.id: "PROVEN"},
                   {claim.id: "human: checked n=2k, m=2l -> n+m=2(k+l); P1 discharged; elementary."},
                   root=ROOT)
    paths = write_reports(exp, str(ROOT))
    return f"manual demo complete -> {paths['markdown']}"


def autonomous_demo() -> str:
    exp = Experiment(id="demo-auto", title="Auto demo (mock provider)",
                     research_question="Smoke-test autonomous runner offline.")
    from intuition_solver.storage.repository import save_experiment
    save_experiment(exp, ROOT)
    M.set_problem(exp, ProblemSpecification(title="Auto", statement="Show n+n=2n for integer n.",
                                            desired_theorem="n+n=2n", proof_obligations=["P1"],
                                            research_objective="smoke test"), root=ROOT)
    rep = run_autonomous(exp, MockProvider(), stop_after="audit", auto_approve=True,
                         n_solvers=3, root=ROOT)
    return f"autonomous demo: stopped={rep.stopped} reason={rep.reason} calls={rep.model_calls}"


if __name__ == "__main__":
    print(manual_demo())
    print(autonomous_demo())
    print("NOTE: all model texts above are illustrative/mock placeholders, not findings.")
