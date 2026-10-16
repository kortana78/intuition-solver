"""Cross-condition comparison with explicit limitation flags."""

from __future__ import annotations

from .baselines import comparability_warning
from .metrics import compute_metrics
from ..core.experiment import Experiment


def compare_conditions(experiments: list[Experiment]) -> dict:
    rows = []
    for exp in experiments:
        m = compute_metrics(exp)
        rows.append({
            "experiment": exp.id,
            "condition": exp.config.condition.value if hasattr(exp.config.condition, "value") else str(exp.config.condition),
            "title": exp.title,
            "metrics": m,
        })
    warning = comparability_warning([{"condition": r["condition"]} for r in rows])
    limitations = [
        "Models, budgets, problem sets, and evaluation criteria should be comparable; document deviations.",
        "Do not calculate success rates from missing, incomparable, or incomplete experiments.",
    ]
    if warning:
        limitations.insert(0, warning)
    return {"rows": rows, "limitations": limitations,
            "conclusion": "No conclusion licensed without complete, comparable experiments."}
