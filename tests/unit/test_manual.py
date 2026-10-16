"""Manual workflow tests: full lifecycle with no API key."""

import uuid

from intuition_solver.core.problem import ProblemSpecification
from intuition_solver.workflows import manual as M
from intuition_solver.core.experiment import Experiment


def _exp() -> Experiment:
    return Experiment(id=f"exp-{uuid.uuid4().hex[:6]}", title="t", research_question="q")


def test_manual_lifecycle_tmp(tmp_path):
    root = tmp_path / "exps"
    exp = M.create_experiment("e1", "Demo", "Does analogy help?", root=root)
    M.set_problem(exp, ProblemSpecification(title="Demo", statement="Prove that the sum of two even numbers is even.",
                                            desired_theorem="even+even=even",
                                            proof_obligations=["P1: show closure"],
                                            research_objective="test pipeline"), root=root)
    a = M.generate_analogy(exp, domain="resource allocation", root=root)
    assert a.blind_prompt and a.audit_prompt
    M.approve_analogy(exp, a.id, root=root)
    prompts = M.export_solver_prompts(exp, a.id, 3, root=root)
    assert len(prompts) == 3
    # blind prompts must not contain the word 'even' if it were forbidden... here check mechanics
    for i, p in enumerate(prompts):
        M.import_solver_response(
            exp, a.id, f"solver-{i+1}",
            "INTERPRETATION: x\nPROPOSED_SOLUTION: y\nCANDIDATE_LEMMAS:\n- L1: pairing insight\n"
            "REASONING: r\nALTERNATIVES:\n- alt\nCOUNTEREXAMPLES:\n- none\nUNRESOLVED:\n- u\n"
            "CONFIDENCE: Low\nPROOF_STATUS: conjecture",
            model_name=f"manual-model-{i+1}", root=root)
    assert len(exp.solver_responses) == 3
    cx = M.cross_examine_prompts(exp, a.id, root=root)
    assert len(cx) == 3
    M.import_dialogue_turn(exp, "critic", "challenge text", root=root)
    prompt = M.reconstruction_prompt(exp, a.id, ["pairing insight"])
    rec = M.import_reconstruction(exp, prompt, "CLAIM: even+even=even.\nDERIVATION: 2a+2b=2(a+b).", root=root)
    assert len(rec.claims) == 1
    # PROVEN without sign-off must fail
    import pytest
    with pytest.raises(ValueError):
        M.audit_claims(exp, {rec.claims[0].id: "PROVEN"}, {rec.claims[0].id: "looks good"}, root=root)
    recs = M.audit_claims(exp, {rec.claims[0].id: "PROVEN"},
                          {rec.claims[0].id: "human: checked 2a+2b=2(a+b) step, obligations P1 discharged"}, root=root)
    assert recs[0].status.value == "PROVEN"
