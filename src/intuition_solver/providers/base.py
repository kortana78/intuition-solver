"""Provider abstraction: common interface for model APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ProviderResponse:
    text: str
    model: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderError(Exception):
    message: str
    retryable: bool = True

    def __str__(self) -> str:
        return self.message


class BaseProvider:
    name: str = "base"

    def complete(self, prompt: str, *, model: str = "", max_tokens: int = 2000,
                 temperature: float = 0.7, timeout_s: int = 120) -> ProviderResponse:
        raise NotImplementedError

    def is_configured(self) -> bool:
        return True
