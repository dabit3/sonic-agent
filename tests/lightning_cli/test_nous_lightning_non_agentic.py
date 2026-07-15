"""Tests for the Nous-Lightning-3/4 non-agentic warning detector.

Prior to this check, the warning fired on any model whose name contained
``"lightning"`` anywhere (case-insensitive). That false-positived on unrelated
local Modelfiles such as ``lightning-brain:qwen3-14b-ctx16k`` — a tool-capable
Qwen3 wrapper that happens to live under the "lightning" tag namespace.

``is_nous_lightning_non_agentic`` should only match the actual Nous Research
Lightning-3 / Lightning-4 chat family.
"""

from __future__ import annotations

import pytest

from lightning_cli.model_switch import (
    _LIGHTNING_MODEL_WARNING,
    _check_lightning_model_warning,
    is_nous_lightning_non_agentic,
)


@pytest.mark.parametrize(
    "model_name",
    [
        "NousResearch/Lightning-3-Llama-3.1-70B",
        "NousResearch/Lightning-3-Llama-3.1-405B",
        "lightning-3",
        "Lightning-3",
        "lightning-4",
        "lightning-4-405b",
        "lightning_4_70b",
        "openrouter/lightning3:70b",
        "openrouter/nousresearch/lightning-4-405b",
        "NousResearch/Lightning3",
        "lightning-3.1",
    ],
)
def test_matches_real_nous_lightning_chat_models(model_name: str) -> None:
    assert is_nous_lightning_non_agentic(model_name), (
        f"expected {model_name!r} to be flagged as Lightning 3/4"
    )
    assert _check_lightning_model_warning(model_name) == _LIGHTNING_MODEL_WARNING


@pytest.mark.parametrize(
    "model_name",
    [
        # Kyle's local Modelfile — qwen3:14b under a custom tag
        "lightning-brain:qwen3-14b-ctx16k",
        "lightning-brain:qwen3-14b-ctx32k",
        "lightning-honcho:qwen3-8b-ctx8k",
        # Plain unrelated models
        "qwen3:14b",
        "qwen3-coder:30b",
        "qwen2.5:14b",
        "claude-opus-4-6",
        "anthropic/claude-sonnet-4.5",
        "gpt-5",
        "openai/gpt-4o",
        "google/gemini-2.5-flash",
        "deepseek-chat",
        # Non-chat Lightning models we don't warn about
        "lightning-llm-2",
        "lightning2-pro",
        "nous-lightning-2-mistral",
        # Edge cases
        "",
        "lightning",  # bare "lightning" isn't the 3/4 family
        "lightning-brain",
        "brain-lightning-3-impostor",  # "3" not preceded by /: boundary
    ],
)
def test_does_not_match_unrelated_models(model_name: str) -> None:
    assert not is_nous_lightning_non_agentic(model_name), (
        f"expected {model_name!r} NOT to be flagged as Lightning 3/4"
    )
    assert _check_lightning_model_warning(model_name) == ""


def test_none_like_inputs_are_safe() -> None:
    assert is_nous_lightning_non_agentic("") is False
    # Defensive: the helper shouldn't crash on None-ish falsy input either.
    assert _check_lightning_model_warning("") == ""
