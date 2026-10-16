"""Correspondence-map helpers shared by analogy generation and reconstruction."""

from __future__ import annotations

from .analogy import Analogy


def correspondence_table_markdown(analogy: Analogy) -> str:
    lines = ["| Original element | Analogy element | Preservation | Notes |", "|---|---|---|---|"]
    if not analogy.correspondence:
        return "_No correspondence entries recorded._"
    for c in analogy.correspondence:
        lines.append(
            f"| {c.original_element} | {c.analogy_element} | {c.preservation} | {c.notes} |"
        )
    return "\n".join(lines)


def preservation_summary(analogy: Analogy) -> str:
    parts = []
    if analogy.preserved_properties:
        parts.append("Must preserve: " + "; ".join(analogy.preserved_properties))
    if analogy.lost_properties:
        parts.append("Approximate/lost: " + "; ".join(analogy.lost_properties))
    if analogy.introduced_assumptions:
        parts.append("Introduced assumptions: " + "; ".join(analogy.introduced_assumptions))
    return "\n".join(parts) if parts else "_No preservation requirements recorded._"
