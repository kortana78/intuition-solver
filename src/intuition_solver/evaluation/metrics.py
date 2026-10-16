"""Evaluation metrics for hypothesis testing (Stages: validity, lemmas, diversity, cost)."""

from __future__ import annotations

import re
from collections import Counter

from ..core.claims import ClaimRecord
from ..core.experiment import Experiment
from ..core.statuses import VerificationStatus


def _words(text: str) -> set[str]:
    return set(w.lower() for w in re.findall(r"[a-zA-Z]{3,}", text))


def lemma_count(exp: Experiment) -> int:
    n = sum(len(r.candidate_lemmas) for r in exp.solver_responses)
    for rec in exp.reconstructions:
        n += len(rec.claims)
    return n


def validity_breakdown(exp: Experiment) -> dict[str, int]:
    c: Counter = Counter()
    for rec in exp.reconstructions:
        for claim in rec.claims:
            c[claim.verification.value] += 1
    for v in VerificationStatus:
        c.setdefault(v.value, 0)
    return dict(c)


def approach_diversity(exp: Experiment) -> dict:
    """Jaccard-based diversity over solver response vocabularies. Higher = more diverse."""
    docs = [_words(r.raw_response) for r in exp.solver_responses if r.raw_response.strip()]
    if len(docs) < 2:
        return {"mean_pairwise_jaccard_distance": 0.0, "n_docs": len(docs),
                "note": "need >=2 responses for diversity"}
    import itertools

    dists = []
    for a, b in itertools.combinations(docs, 2):
        union = a | b
        inter = a & b
        dists.append(1.0 - (len(inter) / len(union) if union else 0.0))
    return {"mean_pairwise_jaccard_distance": sum(dists) / len(dists),
            "n_docs": len(docs), "pairs": len(dists)}


def counterexample_count(exp: Experiment) -> int:
    n = sum(len(r.counterexamples) for r in exp.solver_responses)
    for rec in exp.reconstructions:
        for cl in rec.claims:
            n += len(cl.counterexamples)
    return n


def cost_summary(exp: Experiment) -> dict:
    return {"model_calls": exp.model_calls_made, "tokens_used": exp.tokens_used,
            "events": len(exp.events)}


def compute_metrics(exp: Experiment) -> dict:
    return {
        "lemma_count": lemma_count(exp),
        "validity": validity_breakdown(exp),
        "diversity": approach_diversity(exp),
        "counterexamples": counterexample_count(exp),
        "cost": cost_summary(exp),
        "incomplete": exp.incomplete_stages(),
        "warning": "Do not compute success rates from missing/incomparable experiments.",
    }
