"""Evaluation, verification runner, storage round-trip tests."""

from intuition_solver.core.experiment import Experiment
from intuition_solver.evaluation.metrics import compute_metrics
from intuition_solver.evaluation.reports import build_report_markdown
from intuition_solver.storage.repository import save_experiment, load_experiment
from intuition_solver.verification.runner import run_finite_check
from intuition_solver.workflows import manual as M
from intuition_solver.core.problem import ProblemSpecification


def test_metrics_and_report(tmp_path):
    root = tmp_path / "exps"
    exp = M.create_experiment("m1", "Metrics", root=root)
    M.set_problem(exp, ProblemSpecification(title="M", statement="s", desired_theorem="t",
                                            proof_obligations=["P1"],
                                            research_objective="o"), root=root)
    m = compute_metrics(exp)
    assert m["lemma_count"] == 0
    assert "warning" in m
    md = build_report_markdown(exp)
    assert "Limitations" in md


def test_finite_check():
    ok = run_finite_check("result = all((n + n) % 2 == 0 for n in range(100))")
    assert ok.passed
    bad = run_finite_check("assert 1 == 2")
    assert not bad.passed


def test_storage_roundtrip(tmp_path):
    root = tmp_path / "exps"
    exp = M.create_experiment("s1", "Store", root=root)
    loaded = load_experiment("s1", root)
    assert loaded.id == "s1"
