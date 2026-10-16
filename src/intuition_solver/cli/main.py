"""CLI: intuition init/show/generate-analogy/export-prompts/import-response/...

Manual mode needs no API key. Autonomous `run`/`resume` use the provider abstraction.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from ..agents.analogy_generator import ANALOGY_DOMAINS
from ..core.experiment import Experiment
from ..core.problem import ProblemSpecification
from ..core.statuses import AutonomyLevel, ConditionKind
from ..evaluation.reports import build_report_markdown, write_reports
from ..evaluation.metrics import compute_metrics
from ..evaluation.comparison import compare_conditions
from ..evaluation.baselines import baseline_template
from ..providers.registry import available_providers, create_provider
from ..storage.repository import list_experiments, load_experiment, save_experiment
from ..verification.runner import run_finite_check
from ..workflows import manual as M
from ..workflows.autonomous import run_autonomous, resume_autonomous

app = typer.Typer(help="Intuition Solver: analogy-mediated mathematical exploration.")
console = Console()


def get_root() -> Path:
    return Path(os.environ.get("INTUITION_ROOT", "experiments"))


ROOT = get_root()  # default; refreshed per-invocation by callback below


@app.callback()
def _refresh_root() -> None:
    """Re-resolve the workspace root so INTUITION_ROOT overrides apply per command."""
    global ROOT
    ROOT = get_root()


def _load(exp_id: str) -> Experiment:
    return load_experiment(exp_id, ROOT)


def _save(exp: Experiment) -> None:
    save_experiment(exp, ROOT)


@app.command("init")
def init(
    title: str = typer.Option(..., "--title", "-t", help="Experiment title"),
    exp_id: str = typer.Option("", "--id", help="Experiment id (auto-generated if empty)"),
    research_question: str = typer.Option("", "--question", "-q"),
    problem_file: str = typer.Option("", "--problem-file", help="Markdown/text file with problem statement"),
    statement: str = typer.Option("", "--statement", help="Inline problem statement"),
):
    """Create a new experiment."""
    eid = exp_id or f"exp-{uuid.uuid4().hex[:8]}"
    exp = M.create_experiment(eid, title, research_question, ROOT)
    if problem_file or statement:
        text = Path(problem_file).read_text(encoding="utf-8") if problem_file else statement
        M.set_problem(exp, ProblemSpecification(title=title, statement=text,
                                                research_objective=research_question), ROOT)
    console.print(f"[green]Created experiment {eid}[/green] in {ROOT / eid}")
    console.print("Next: intuition show --id %s" % eid)


@app.command("show")
def show(exp_id: str = typer.Option(..., "--id", help="Experiment id")):
    """Show experiment status, stage, and outstanding obligations."""
    exp = _load(exp_id)
    console.print(f"[bold]{exp.title}[/bold] ({exp.id})  stage={exp.stage.value}")
    console.print(f"Research question: {exp.research_question or '(none)'}")
    t = Table("Area", "Detail")
    t.add_row("problem", exp.problem.title if exp.problem else "(missing)")
    t.add_row("analogies", ", ".join(f"{a.id} ({a.domain}, approved={a.approved})" for a in exp.analogies) or "(none)")
    t.add_row("responses", str(len(exp.solver_responses)))
    t.add_row("dialogue turns", str(len(exp.dialogue)))
    t.add_row("reconstructions", str(len(exp.reconstructions)))
    t.add_row("verifications", str(len(exp.verifications)))
    t.add_row("model calls", str(exp.model_calls_made))
    console.print(t)
    missing = exp.incomplete_stages()
    if missing:
        console.print("[yellow]Incomplete:[/yellow]")
        for m in missing:
            console.print(f"  - [ ] {m}")
    else:
        console.print("[green]All pipeline stages have records.[/green]")
    if exp.problem:
        for w in exp.problem.validate_completeness():
            console.print(f"[yellow]problem warning: {w}[/yellow]")


@app.command("generate-analogy")
def generate_analogy(
    exp_id: str = typer.Option(..., "--id"),
    domain: str = typer.Option("networks and graph structures", "--domain", "-d",
                               help=f"One of: {', '.join(ANALOGY_DOMAINS)}"),
    title: str = typer.Option("", "--title"),
):
    """Draft an analogy skeleton (researcher edits before approval)."""
    exp = _load(exp_id)
    a = M.generate_analogy(exp, domain=domain, title=title, root=ROOT)
    console.print(f"[green]Analogy {a.id}[/green] domain={a.domain}")
    console.print("Blind prompt preview:")
    console.print(a.blind_prompt[:1500])
    if a.leakage and not a.leakage.passed:
        console.print("[red]Leakage findings:[/red]")
        for f in a.leakage.findings:
            console.print(f"  - {f.term}: ...{f.context[:100]}...")
    console.print("Edit experiments/%s/experiment.json (analogy_statement/objects/...) then approve." % exp.id)


@app.command("approve-analogy")
def approve_analogy(exp_id: str = typer.Option(..., "--id"), analogy: str = typer.Option(..., "--analogy", "-a")):
    exp = _load(exp_id)
    a = M.approve_analogy(exp, analogy, ROOT)
    console.print(f"[green]Approved {a.id}[/green]")


@app.command("export-prompts")
def export_prompts(
    exp_id: str = typer.Option(..., "--id"),
    analogy: str = typer.Option(..., "--analogy", "-a"),
    n: int = typer.Option(3, "--n", help="Number of independent solver prompts"),
    out: str = typer.Option("", "--out", help="Directory to write prompt files"),
):
    """Export blind independent-solver prompts for manual use in external AI tools."""
    exp = _load(exp_id)
    prompts = M.export_solver_prompts(exp, analogy, n, root=ROOT)
    outdir = Path(out) if out else ROOT / exp_id / "prompts"
    outdir.mkdir(parents=True, exist_ok=True)
    for p in prompts:
        (outdir / f"{p['solver']}_blind.md").write_text(p["blind_prompt"], encoding="utf-8")
    # cross-exam prompts
    for c in M.cross_examine_prompts(exp, analogy, root=ROOT):
        (outdir / f"cross_{c['role']}.md").write_text(c["prompt"], encoding="utf-8")
    recon = M.reconstruction_prompt(exp, analogy, [])
    (outdir / "reconstruction.md").write_text(recon, encoding="utf-8")
    console.print(f"[green]Wrote {len(prompts)} blind prompts + cross-exam + reconstruction to {outdir}[/green]")
    console.print("Copy each blind prompt into a separate external model. Do not reveal the original problem.")


@app.command("import-response")
def import_response(
    exp_id: str = typer.Option(..., "--id"),
    analogy: str = typer.Option(..., "--analogy", "-a"),
    solver: str = typer.Option("solver-1", "--solver", "-s"),
    file: str = typer.Option(..., "--file", "-f", help="Markdown/text file with the model's response"),
    model: str = typer.Option("external-manual", "--model"),
    version: str = typer.Option("", "--model-version"),
):
    """Import one independently collected model response (preserved verbatim)."""
    exp = _load(exp_id)
    sr = M.import_solver_response(exp, analogy, solver, "", model_name=model,
                                  model_version=version, from_file=file, root=ROOT)
    console.print(f"[green]Imported {sr.id}[/green] lemmas={len(sr.candidate_lemmas)}")


@app.command("cross-examine")
def cross_examine(
    exp_id: str = typer.Option(..., "--id"),
    analogy: str = typer.Option(..., "--analogy", "-a"),
    role: str = typer.Option(..., "--role", help="critic|counterexample_hunter|alternative_explorer|synthesizer|research_controller"),
    file: str = typer.Option(..., "--file", "-f"),
    model: str = typer.Option("external-manual", "--model"),
):
    exp = _load(exp_id)
    turn = M.import_dialogue_turn(exp, role, "", author_model=model, from_file=file, root=ROOT)
    console.print(f"[green]Recorded dialogue turn {turn.id} ({role})[/green]")


@app.command("reconstruct")
def reconstruct(
    exp_id: str = typer.Option(..., "--id"),
    analogy: str = typer.Option(..., "--analogy", "-a"),
    file: str = typer.Option(..., "--file", "-f", help="Reconstruction model response file"),
    insight: list[str] = typer.Option([], "--insight", help="Selected insight (repeatable)"),
    model: str = typer.Option("external-manual", "--model"),
    print_prompt: bool = typer.Option(False, "--print-prompt"),
):
    exp = _load(exp_id)
    prompt = M.reconstruction_prompt(exp, analogy, insight)
    if print_prompt:
        console.print(prompt)
    rec = M.import_reconstruction(exp, prompt, "", model_name=model, from_file=file, root=ROOT)
    console.print(f"[green]Reconstruction {rec.id}[/green] with {len(rec.claims)} candidate claim(s)")


@app.command("audit")
def audit(
    exp_id: str = typer.Option(..., "--id"),
    set_status: list[str] = typer.Option([], "--set", help="claim_id=STATUS (repeatable)"),
    note: list[str] = typer.Option([], "--note", help="claim_id=text (repeatable)"),
    finite: str = typer.Option("", "--finite", help="Python file with finite-case check; sets result var"),
    claim: str = typer.Option("", "--claim", help="Claim id the finite check supports"),
):
    """Human-led proof audit. PROVEN requires a human/Lean sign-off note."""
    exp = _load(exp_id)
    decisions = dict(s.split("=", 1) for s in set_status) if set_status else {}
    notes: dict[str, str] = {}
    for n in note:
        k, v = n.split("=", 1)
        notes[k] = v
    finite_results: dict[str, str] = {}
    if finite:
        code = Path(finite).read_text(encoding="utf-8")
        oc = run_finite_check(code)
        console.print(f"finite check passed={oc.passed}\n{oc.output[:2000]}")
        if claim:
            finite_results[claim] = f"passed={oc.passed}: {oc.output[:500]}"
            if oc.passed and claim not in decisions:
                decisions[claim] = "COMPUTATIONALLY_SUPPORTED"
    recs = M.audit_claims(exp, decisions or None, notes or None,
                          finite_results or None, ROOT)
    for v in recs:
        console.print(f"{v.claim_id}: {v.status.value} ({v.method})")


@app.command("report")
def report(exp_id: str = typer.Option(..., "--id"), out: str = typer.Option("", "--out")):
    exp = _load(exp_id)
    paths = write_reports(exp, out or str(ROOT / exp_id))
    console.print(f"[green]Report written:[/green] {paths['markdown']}, {paths['json']}")


@app.command("evaluate")
def evaluate(exp_id: str = typer.Option("", "--id", help="Single experiment, or empty for all"),
             compare: bool = typer.Option(False, "--compare", help="Compare all experiments by condition")):
    if compare:
        exps = [load_experiment(e, ROOT) for e in list_experiments(ROOT)]
        console.print(json.dumps(compare_conditions(exps), indent=2)[:6000])
        return
    exp = _load(exp_id)
    console.print(json.dumps(compute_metrics(exp), indent=2))


@app.command("baseline")
def baseline(
    exp_id: str = typer.Option(..., "--id"),
    condition: str = typer.Option(..., "--condition", help="A_direct_single|B_direct_multi|C_analogy_no_dialogue|D_full_architecture"),
    file: str = typer.Option("", "--file", help="JSON file with baseline record fields"),
):
    """Record a baseline (conditions A-D) for controlled comparison."""
    exp = _load(exp_id)
    rec = baseline_template(condition)
    if file:
        rec.update(json.loads(Path(file).read_text(encoding="utf-8")))
    exp.baselines[condition] = rec
    exp.touch("baseline", {"condition": condition})
    _save(exp)
    console.print(f"[green]Recorded baseline {condition}[/green]")


@app.command("run")
def run(
    exp_id: str = typer.Option(..., "--id"),
    provider: str = typer.Option("mock", "--provider", help=f"One of: {', '.join(available_providers())}"),
    model: str = typer.Option("", "--model"),
    autonomy: int = typer.Option(3, "--autonomy", help="0 manual, 1 assisted, 2 supervised, 3 autonomous"),
    max_calls: int = typer.Option(30, "--max-calls"),
    stop_after: str = typer.Option("audit", "--stop-after", help="analogy|solved|cross_exam|audit"),
    auto_approve: bool = typer.Option(False, "--yes", "-y", help="Auto-approve checkpoints"),
    solvers: int = typer.Option(3, "--solvers"),
):
    """Autonomous execution of the pipeline via a model provider."""
    exp = _load(exp_id)
    try:
        exp.config.autonomy_level = AutonomyLevel(autonomy)
    except ValueError:
        raise typer.BadParameter("autonomy must be 0-3")
    exp.config.budgets.max_model_calls = max_calls
    exp.config.provider = provider
    _save(exp)
    prov = create_provider(provider)
    if provider != "mock" and not prov.is_configured():
        console.print("[red]Provider not configured.[/red] Set OPENAI_API_KEY/OPENAI_BASE_URL or use manual mode.")
        raise typer.Exit(2)
    rep = run_autonomous(exp, prov, stop_after=stop_after, auto_approve=auto_approve or autonomy == 3,
                         model=model, n_solvers=solvers, root=ROOT)
    console.print(f"stopped={rep.stopped} reason={rep.reason or '(completed)'} calls={rep.model_calls}")
    console.print(f"stages: {', '.join(rep.stages_completed) or '(none new; resume state preserved)'}")


@app.command("resume")
def resume(
    exp_id: str = typer.Option(..., "--id"),
    provider: str = typer.Option("mock", "--provider"),
    auto_approve: bool = typer.Option(False, "--yes", "-y"),
):
    """Resume an interrupted run from the last completed stage."""
    exp = _load(exp_id)
    prov = create_provider(provider)
    rep = resume_autonomous(exp, prov, auto_approve=auto_approve, root=ROOT)
    console.print(f"stopped={rep.stopped} reason={rep.reason or '(completed)'} calls={rep.model_calls}")


@app.command("export")
def export(exp_id: str = typer.Option(..., "--id"), out: str = typer.Option("", "--out")):
    """Export anonymized experiment JSON (secrets stripped) for publication."""
    from ..storage.repository import export_anonymized
    exp = _load(exp_id)
    data = export_anonymized(exp)
    p = Path(out) if out else ROOT / exp_id / f"{exp_id}_export.json"
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")
    console.print(f"[green]Exported to {p}[/green]")


@app.command("set-problem")
def set_problem(exp_id: str = typer.Option(..., "--id"), file: str = typer.Option(..., "--file")):
    """Attach a problem specification from a JSON or Markdown file."""
    exp = _load(exp_id)
    text = Path(file).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
        prob = ProblemSpecification(**data)
    except Exception:
        prob = ProblemSpecification(title=exp.title, statement=text)
    M.set_problem(exp, prob, ROOT)
    console.print("[green]Problem specification saved.[/green]")


@app.command("note")
def note(exp_id: str = typer.Option(..., "--id"), text: str = typer.Option(..., "--text")):
    exp = _load(exp_id)
    M.add_note(exp, text, ROOT)
    console.print("[green]Note recorded.[/green]")


@app.command("providers")
def providers():
    console.print("Available providers: " + ", ".join(available_providers()))
