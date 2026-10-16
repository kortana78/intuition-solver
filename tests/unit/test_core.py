"""Core model tests: problem spec, leakage checker, claim lifecycle."""

from intuition_solver.core.analogy import check_blind_leakage
from intuition_solver.core.problem import ProblemSpecification


def test_problem_completeness_warnings():
    p = ProblemSpecification(title="t", statement="")
    w = p.validate_completeness()
    assert any("statement" in x.lower() for x in w)


def test_forbidden_terms_and_leakage():
    p = ProblemSpecification(
        title="Goldbach Conjecture exploration",
        statement="Every even integer > 2 is the sum of two primes.",
        notation=["p_n", "zeta"],
        desired_theorem="Prove Goldbach",
    )
    terms = p.forbidden_terms()
    assert any("goldbach" in t.lower() for t in terms)
    bad = "This Goldbach analogy uses p_n everywhere."
    rep = check_blind_leakage(bad, terms)
    assert not rep.passed and rep.findings
    good = "A delivery network must pair parcels at depots under capacity limits."
    rep2 = check_blind_leakage(good, terms)
    assert rep2.passed
