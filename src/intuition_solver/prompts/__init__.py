"""Prompt-template loader + renderer. Templates live as Markdown files in this package."""

from __future__ import annotations

import importlib.resources as _resources
from string import Template

TEMPLATE_FILES = {
    "problem_specification": "problem_specification.md",
    "analogy_generation": "analogy_generation.md",
    "analogy_audit": "analogy_audit.md",
    "independent_solver": "independent_solver.md",
    "cross_examination": "cross_examination.md",
    "reconstruction": "reconstruction.md",
    "proof_audit": "proof_audit.md",
}

VERSION = "v1"


def load_template(name: str) -> str:
    filename = TEMPLATE_FILES[name]
    ref = _resources.files(__package__).joinpath(filename)
    return ref.read_text(encoding="utf-8")


def render(name: str, **kwargs) -> str:
    """Render a template with $VARIABLE substitution. Unknown vars left intact safely."""
    text = load_template(name)
    # Use safe_substitute so missing keys don't crash manual prompt building.
    out = Template(text).safe_substitute(**kwargs)
    return out


def prompt_version(name: str) -> str:
    return f"{name}:{VERSION}"
