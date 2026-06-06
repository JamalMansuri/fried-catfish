"""Inference layer.

One LLMClient abstraction, two backends resolved at startup:
  - FakeLLM      : deterministic fixtures; the zero-install demo path (CATFISH_DEMO=1).
  - AnthropicLLM : live path via CATFISH_LLM_API_KEY + CATFISH_MODEL (lazy-imports `anthropic`).

Tournament code calls `complete(task, prompt, json=..., meta=...)`. `task` routes the FakeLLM;
the real backend sends `prompt`/`system` to the model. `meta` carries deterministic routing hints
the FakeLLM uses and the real backend ignores.
"""
from __future__ import annotations

import json as _json
import os
import re
import time
from typing import Any, Optional

from . import fixtures

# task tags
GENERATE = "GENERATE"
REFLECT = "REFLECT"
RANK = "RANK"
EVOLVE = "EVOLVE"
META = "META"
CARD = "CARD"


class LLMError(RuntimeError):
    pass


class BaseLLM:
    name = "base"

    def complete(self, task: str, prompt: str, *, system: Optional[str] = None,
                 json: bool = False, meta: Optional[dict] = None,
                 max_tokens: int = 1200, temperature: float = 0.3) -> Any:
        raise NotImplementedError


# --------------------------------------------------------------------- Fake

class FakeLLM(BaseLLM):
    """Deterministic fixtures so `CATFISH_DEMO=1` runs free, instant, offline, repeatable."""
    name = "fake-demo"

    def complete(self, task, prompt, *, system=None, json=False, meta=None,
                 max_tokens=1200, temperature=0.3):
        meta = meta or {}
        if task == GENERATE:
            return [dict(c) for c in fixtures.DEMO_CANDIDATES]
        if task == REFLECT:
            return fixtures.critique(meta.get("name", ""), meta.get("role", "neutral"))
        if task == RANK:
            return fixtures.rank(meta.get("a_name", ""), meta.get("b_name", ""))
        if task == EVOLVE:
            return []                                  # no new candidates in the demo
        if task == META:
            return dict(fixtures.DEMO_META)
        if task == CARD:
            return dict(fixtures.DEMO_CARD)
        raise LLMError(f"FakeLLM has no fixture for task {task!r}")


# ---------------------------------------------------------------- Anthropic

_JSON_RE = re.compile(r"(\{.*\}|\[.*\])", re.DOTALL)


def _extract_json(text: str) -> Any:
    m = _JSON_RE.search(text)
    if not m:
        raise LLMError(f"expected JSON in model output, got: {text[:200]!r}")
    return _json.loads(m.group(1))


class AnthropicLLM(BaseLLM):
    name = "anthropic"

    def __init__(self, model: str, api_key: str):
        try:
            import anthropic  # lazy: not needed for the demo path
        except ImportError as e:
            raise LLMError("live path needs `pip install catfish[live]` (the anthropic SDK)") from e
        self._client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.name = f"anthropic:{model}"

    def complete(self, task, prompt, *, system=None, json=False, meta=None,
                 max_tokens=1200, temperature=0.3):
        sys = system or ""
        if json:
            sys = (sys + "\nReturn ONLY valid JSON. No prose, no markdown fences.").strip()
        last = None
        for attempt in range(3):
            try:
                resp = self._client.messages.create(
                    model=self.model, max_tokens=max_tokens, temperature=temperature,
                    system=sys or None,
                    messages=[{"role": "user", "content": prompt}],
                )
                text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
                return _extract_json(text) if json else text.strip()
            except Exception as e:  # noqa: BLE001 - retry transient errors
                last = e
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
        raise LLMError(f"anthropic call failed for task {task}: {last}")


# ------------------------------------------------------------------ resolve

def resolve_llm() -> BaseLLM:
    """Pick a backend. Demo wins; else a key is required (server prints a friendly message)."""
    if os.environ.get("CATFISH_DEMO") == "1":
        return FakeLLM()
    key = os.environ.get("CATFISH_LLM_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise LLMError(
            "no LLM configured. Set CATFISH_DEMO=1 for the free offline demo, "
            "or set CATFISH_LLM_API_KEY (+ optional CATFISH_MODEL) for a live run."
        )
    model = os.environ.get("CATFISH_MODEL", "claude-sonnet-4-6")
    return AnthropicLLM(model=model, api_key=key)
