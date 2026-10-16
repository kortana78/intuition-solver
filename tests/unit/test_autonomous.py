"""Autonomous runner tests with the deterministic mock provider."""

from intuition_solver.core.experiment import Experiment
from intuition_solver.core.problem import ProblemSpecification
from intuition_solver.providers.mock import MockProvider
from intuition_solver.workflows import manual as M
from intuition_solver.workflows.autonomous import run_autonomous


def test_autonomous_mock_respects_budgets(tmp_path):
    root = tmp_path / "exps"
    exp = M.create_experiment("au1", "Auto demo", "q", root=root)
    M.set_problem(exp, ProblemSpecification(title="Auto demo", statement="Show n+n=2n.",
                                            desired_theorem="n+n=2n",
                                            proof_obligations=["P1"],
                                            research_objective="demo"), root=root)
    exp.config.budgets.max_model_calls = 4
    rep = run_autonomous(exp, MockProvider(), stop_after="audit", auto_approve=True,
                         n_solvers=2, root=root)
    assert rep.model_calls <= 4
    assert rep.stopped in (True, False)
    # resume must not duplicate solver responses beyond need
    n_before = len(exp.solver_responses)
    rep2 = run_autonomous(exp, MockProvider(), stop_after="audit", auto_approve=True,
                          n_solvers=2, root=root)
    assert len(exp.solver_responses) == n_before


def test_independence_blind():
    from intuition_solver.agents.base import SolverAgent
    from intuition_solver.core.analogy import Analogy
    a = Analogy(id="a", experiment_id="e", domain="networks",
                analogy_statement="Route parcels.", objective="minimise trips")
    prompt = SolverAgent().build_prompt(a)
    assert "parcel" in prompt.lower()
    assert "Goldbach" not in prompt
