"""Markdown + JSON experiment reports."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from ..core.correspondence import correspondence_table_markdown
from ..core.experiment import Experiment
from ..storage.repository import export_anonymized
from .metrics import compute_metrics


def build_report_dict(exp: Experiment) -> dict:
    return {
        "experiment": exp.id,
        "title": exp.title,
        "research_question": exp.research_question,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stage": exp.stage.value if hasattr(exp.stage, "value") else str(exp.stage),
        "config": exp.config.model_dump(),
        "problem": exp.problem.model_dump() if exp.problem else None,
        "analogies": [a.model_dump() for a in exp.analogies],
        "solver_responses": [r.model_dump() for r in exp.solver_responses],
        "dialogue": [t.model_dump() for t in exp.dialogue],
        "reconstructions": [r.model_dump() for r in exp.reconstructions],
        "verifications": [v.model_dump() for v in exp.verifications],
        "baselines": exp.baselines,
        "researcher_notes": exp.researcher_notes,
        "metrics": compute_metrics(exp),
        "incomplete_stages": exp.incomplete_stages(),
        "limitations": [
            "Model confidence is not evidence; majority agreement is not proof.",
            "Finite tests are not proofs of unrestricted statements.",
            "Novelty requires documented literature review; never fabricate references.",
            "Automated blind-mode checks are heuristic; semantic concealment needs human audit.",
        ],
    }


def build_report_markdown(exp: Experiment) -> str:
    d = build_report_dict(exp)
    L: list[str] = []
    L.append(f"# Experiment Report: {exp.title} (`{exp.id}`)")
    L.append("")
    L.append(f"Research question: {exp.research_question or '(none)'}")
    L.append(f"Stage: `{d['stage']}` | Generated: {d['generated_at']}")
    L.append("")
    L.append("## 1. Problem")
    if exp.problem:
        L.append(f"**{exp.problem.title}**")
        L.append("")
        L.append(exp.problem.statement)
        L.append("")
        L.append(f"Desired theorem: {exp.problem.desired_theorem or '(none)'}")
        L.append(f"Proof obligations: {'; '.join(exp.problem.proof_obligations) or '(none)'}")
    else:
        L.append("_(no problem specification)_")
    L.append("")
    L.append("## 2. Analogies")
    if not exp.analogies:
        L.append("_(none)_")
    for a in exp.analogies:
        L.append(f"### {a.title} (`{a.id}`, domain: {a.domain}, approved: {a.approved})")
        L.append(a.analogy_statement)
        L.append("")
        L.append(correspondence_table_markdown(a))
        if a.leakage and not a.leakage.passed:
            L.append("")
            L.append("**Leakage findings (must fix before blind export):**")
            for f in a.leakage.findings:
                L.append(f"- `{f.term}` ... `{f.context[:120]}`")
    L.append("")
    L.append("## 3. Independent solver responses (raw preserved)")
    for r in exp.solver_responses:
        L.append(f"### {r.solver_name} ({r.model_name})")
        L.append(f"<details><summary>prompt {r.prompt_version}</summary>\n\n{r.prompt_text}\n\n</details>")
        L.append("")
        L.append(r.raw_response)
        L.append("")
    L.append("## 4. Cross-examination")
    for t in exp.dialogue:
        L.append(f"### {t.role} ({t.author_model})")
        L.append(t.response_text)
        L.append("")
    L.append("## 5. Reconstruction and claims")
    for rec in exp.reconstructions:
        L.append(f"### {rec.id} ({rec.model_name})")
        for cl in rec.claims:
            L.append(f"- **{cl.id}** [{cl.verification.value}] {cl.statement[:300]}")
        if rec.rejected_ideas:
            L.append("Rejected: " + "; ".join(rec.rejected_ideas))
    L.append("")
    L.append("## 6. Verification")
    for v in exp.verifications:
        L.append(f"- {v.claim_id}: **{v.status.value}** via {v.method}: {v.notes[:300]}")
    if not exp.verifications:
        L.append("_(no verification records; all claims UNVERIFIED)_")
    L.append("")
    L.append("## 7. Metrics")
    L.append("```json")
    L.append(json.dumps(d["metrics"], indent=2))
    L.append("```")
    L.append("")
    L.append("## 8. Baselines / comparison")
    L.append("```json")
    L.append(json.dumps(exp.baselines or {}, indent=2)[:4000])
    L.append("```")
    L.append("")
    L.append("## 9. Researcher notes")
    for n in exp.researcher_notes:
        L.append(f"- {n}")
    L.append("")
    L.append("## 10. Limitations")
    for lim in d["limitations"]:
        L.append(f"- {lim}")
    L.append("")
    L.append("## 11. Incomplete stages")
    for s in d["incomplete_stages"]:
        L.append(f"- [ ] {s}")
    if not d["incomplete_stages"]:
        L.append("- [x] all pipeline stages have records")
    return "\n".join(L)


def write_reports(exp: Experiment, out_dir: str = ".") -> dict[str, str]:
    from pathlib import Path
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    md = build_report_markdown(exp)
    js = export_anonymized(exp)
    md_path = p / f"{exp.id}_report.md"
    json_path = p / f"{exp.id}_report.json"
    md_path.write_text(md, encoding="utf-8")
    json_path.write_text(json.dumps(js, indent=2), encoding="utf-8")
    return {"markdown": str(md_path), "json": str(json_path)}
