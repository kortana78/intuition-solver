"""OpenAI-compatible HTTP provider using only the stdlib (no hard SDK dependency).

Works with OpenAI, Together, OpenRouter, vLLM, Ollama, LM Studio, etc. by setting
OPENAI_BASE_URL / OPENAI_API_KEY. If the optional `openai` SDK is installed it is
preferred; otherwise a urllib fallback is used.
"""

from __future__ import annotations

import json
import os
import urllib.request

from .base import BaseProvider, ProviderError, ProviderResponse


class OpenAICompatibleProvider(BaseProvider):
    name = "openai_compatible"

    def __init__(self, api_key: str = "", base_url: str = "", default_model: str = "") -> None:
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.default_model = default_model or os.environ.get("INTUITION_MODEL", "gpt-4o-mini")

    def is_configured(self) -> bool:
        # Allow keyless local servers (Ollama/LM Studio); only the URL is required.
        return bool(self.base_url)

    def has_key(self) -> bool:
        return bool(self.api_key)

    def complete(self, prompt: str, *, model: str = "", max_tokens: int = 2000,
                 temperature: float = 0.7, timeout_s: int = 120) -> ProviderResponse:
        chosen = model or self.default_model
        # Prefer official SDK when available.
        try:
            import openai  # type: ignore

            client = openai.OpenAI(api_key=self.api_key or None, base_url=self.base_url or None)
            resp = client.chat.completions.create(
                model=chosen,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout_s,
            )
            text = resp.choices[0].message.content or ""
            usage = {}
            try:
                usage = dict(resp.usage) if resp.usage else {}
            except Exception:
                usage = {}
            return ProviderResponse(text=text, model=chosen, usage=usage)
        except ImportError:
            pass
        except Exception as exc:  # SDK present but call failed
            raise ProviderError(f"openai SDK call failed: {exc}", retryable=True) from exc

        # urllib fallback: chat completions endpoint.
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": chosen,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as fh:
                data = json.loads(fh.read().decode("utf-8"))
        except Exception as exc:
            raise ProviderError(f"HTTP provider call failed: {exc}", retryable=True) from exc
        try:
            text = data["choices"][0]["message"]["content"] or ""
        except Exception as exc:
            raise ProviderError(f"Unexpected provider response shape: {exc}", retryable=False) from exc
        return ProviderResponse(text=text, model=chosen, usage=data.get("usage", {}), raw=data)
