"""Integration: CLI manual flow end-to-end (no API key)."""

from typer.testing import CliRunner

from intuition_solver.cli.main import app

runner = CliRunner()


def test_cli_manual_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("INTUITION_ROOT", str(tmp_path / "exps"))
    r = runner.invoke(app, ["init", "--title", "CLI demo", "--id", "cli1",
                            "--statement", "Prove even+even=even."])
    assert r.exit_code == 0, r.output
    r = runner.invoke(app, ["generate-analogy", "--id", "cli1", "--domain", "resource allocation"])
    assert r.exit_code == 0, r.output
    r = runner.invoke(app, ["show", "--id", "cli1"])
    assert r.exit_code == 0 and "cli1" in r.output


def test_cli_providers_list():
    r = runner.invoke(app, ["providers"])
    assert r.exit_code == 0 and "mock" in r.output
