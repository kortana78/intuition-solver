"""Deterministic mock provider for tests, docs, and offline demos.

Never present mock outputs as genuine experimental findings.
"""

from __future__ import annotations

import hashlib

from .base import BaseProvider, ProviderResponse


class MockProvider(BaseProvider):
    name = "mock"

    def __init__(self, tag: str = "mock") -> None:
        self.tag = tag
        self.calls = 0

    def complete(self, prompt: str, *, model: str = "", max_tokens: int = 2000,
                 temperature: float = 0.7, timeout_s: int = 120) -> ProviderResponse:
        self.calls += 1
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
        text = (
            f"[MOCK RESPONSE {self.tag} :: {model or 'mock-model'} :: hash={digest}]\n"
            "INTERPRETATION: deterministic illustrative placeholder.\n"
            "PROPOSED_SOLUTION: partial illustrative sketch only (NOT a real result).\n"
            "CANDIDATE_LEMMAS: L1: illustrative structural observation (placeholder).\n"
            "REASONING: A1 (placeholder assumption): analogy taken at face value for demo.\n"
            "ALTERNATIVES: alternative placeholder approach.\n"
            "COUNTEREXAMPLES: none checked (placeholder).\n"
            "UNRESOLVED: everything substantive remains unresolved.\n"
            "CONFIDENCE: Low. PROOF_STATUS: conjecture.\n"
        )
        return ProviderResponse(
            text=text, model=model or "mock-model",
            usage={"prompt_chars": len(prompt), "mock": True},
        )
