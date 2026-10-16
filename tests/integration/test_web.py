"""Integration: web app smoke test."""

from fastapi.testclient import TestClient

from intuition_solver.web.app import app


def test_web_index():
    c = TestClient(app)
    r = c.get("/")
    assert r.status_code == 200
    assert "Intuition Solver" in r.text
