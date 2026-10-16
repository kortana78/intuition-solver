"""Lightweight local web interface (FastAPI): review experiments, copy prompts, import responses.

Run: uvicorn intuition_solver.web.app:app --reload
Manual mode needs no API key.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from ..evaluation.metrics import compute_metrics
from ..evaluation.reports import build_report_markdown
from ..storage.repository import list_experiments, load_experiment, save_experiment
from ..workflows import manual as M

def get_root() -> Path:
    return Path(os.environ.get("INTUITION_ROOT", "experiments"))


ROOT = get_root()

app = FastAPI(title="Intuition Solver: Research Workspace")


class ImportBody(BaseModel):
    analogy_id: str = ""
    solver: str = "solver-1"
    text: str = ""
    model: str = "external-manual"


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    exps = list_experiments(ROOT)
    items = "".join(f"<li><a href='/exp/{e}'>{e}</a></li>" for e in exps) or "<li>(no experiments yet)</li>"
    return f"""<html><body style='font-family:sans-serif;max-width:800px;margin:2em auto'>
    <h1>Intuition Solver: Research Workspace</h1>
    <p>Manual mode: create experiments via CLI (<code>intuition init</code>), then review here.
    No API key required. Raw prompts/responses preserved; claims stay UNVERIFIED until audited.</p>
    <h2>Experiments</h2><ul>{items}</ul>
    <p><a href='/docs'>API docs</a></p></body></html>"""


@app.get("/exp/{exp_id}")
def exp_view(exp_id: str) -> Any:
    try:
        exp = load_experiment(exp_id, ROOT)
    except FileNotFoundError:
        raise HTTPException(404, f"Experiment {exp_id} not found")
    return {
        "id": exp.id, "title": exp.title, "stage": exp.stage.value,
        "problem": exp.problem.model_dump() if exp.problem else None,
        "analogies": [a.model_dump() for a in exp.analogies],
        "responses": len(exp.solver_responses),
        "dialogue": len(exp.dialogue),
        "verifications": [v.model_dump() for v in exp.verifications],
        "incomplete": exp.incomplete_stages(),
        "metrics": compute_metrics(exp),
    }


@app.get("/exp/{exp_id}/prompts/{analogy_id}")
def exp_prompts(exp_id: str, analogy_id: str) -> Any:
    exp = load_experiment(exp_id, ROOT)
    return {"blind": [p for p in M.export_solver_prompts(exp, analogy_id, 3, root=ROOT)],
            "cross": M.cross_examine_prompts(exp, analogy_id, root=ROOT)}


@app.post("/exp/{exp_id}/import")
def exp_import(exp_id: str, body: ImportBody) -> Any:
    exp = load_experiment(exp_id, ROOT)
    sr = M.import_solver_response(exp, body.analogy_id, body.solver, body.text,
                                  model_name=body.model, root=ROOT)
    return {"id": sr.id, "lemmas": sr.candidate_lemmas}


@app.get("/exp/{exp_id}/report.md")
def exp_report(exp_id: str) -> HTMLResponse:
    exp = load_experiment(exp_id, ROOT)
    md = build_report_markdown(exp)
    return HTMLResponse(f"<pre>{md}</pre>")
