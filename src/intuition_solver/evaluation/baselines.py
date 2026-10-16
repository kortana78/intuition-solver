"""Baseline condition definitions A-D and comparability guardrails."""

from __future__ import annotations

from ..core.statuses import ConditionKind

BASELINES = {
    ConditionKind.DIRECT_SINGLE.value: {
        "label": "A. Direct single-model problem-solving",
        "procedure": "One model answers the original problem directly, no analogy, no dialogue.",
    },
    ConditionKind.DIRECT_MULTI.value: {
        "label": "B. Direct multi-model problem-solving",
        "procedure": "Three models answer the original directly + share; no analogy stage.",
    },
    ConditionKind.ANALOGY_NO_DIALOGUE.value: {
        "label": "C. Analogy-mediated without cross-examination",
        "procedure": "Analogies + independent solvers + reconstruction; skip dialogue.",
    },
    ConditionKind.FULL_ARCHITECTURE.value: {
        "label": "D. Full architecture",
        "procedure": "Analogies + independent solvers + dialogue + reconstruction + verification.",
    },
}


def baseline_template(condition: str) -> dict:
    base = BASELINES.get(condition, {"label": condition, "procedure": ""})
    return {
        "condition": condition, **base,
        "models": [], "problem_id": "", "prompts": [], "raw_outputs": [],
        "proof_validity": "", "lemmas": [], "counterexamples": [],
        "diversity_note": "", "novelty": "", "gaps": [], "researcher_assessment": "",
        "time_spent": "", "token_usage": "", "evidence": [],
    }


def comparability_warning(records: list[dict]) -> str:
    if not records:
        return "No baseline records: comparisons are not licensed."
    conds = {r.get("condition") for r in records}
    if len(conds) < 2:
        return "Only one condition recorded: no comparison can be drawn yet."
    return ""
