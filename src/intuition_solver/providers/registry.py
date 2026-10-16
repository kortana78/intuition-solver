"""Provider registry + factory."""

from __future__ import annotations

import os

from .base import BaseProvider
from .mock import MockProvider
from .openai_compatible import OpenAICompatibleProvider

_REGISTRY: dict[str, type[BaseProvider]] = {
    "mock": MockProvider,
    "openai_compatible": OpenAICompatibleProvider,
    "openai": OpenAICompatibleProvider,
}


def available_providers() -> list[str]:
    return sorted(_REGISTRY)


def create_provider(name: str = "", **kwargs) -> BaseProvider:
    name = (name or os.environ.get("INTUITION_PROVIDER", "mock")).lower()
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown provider '{name}'. Available: {available_providers()}")
    if cls is MockProvider:
        return MockProvider(tag=kwargs.get("tag", "mock"))
    return cls(**kwargs)  # type: ignore[call-arg]
