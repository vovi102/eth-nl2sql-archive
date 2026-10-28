"""Regressions found while preparing the real T11 GPU pipeline."""

import sys
from types import SimpleNamespace

import pytest

from eth_nl2sql import config as cfg
from eth_nl2sql.generation.backend import load_tokenizer, preflight_generation


@pytest.mark.parametrize("advertised,expected", [(10**30, 8192), (4096, 4096)])
def test_real_model_context_bounds_tokenizer_sentinel(monkeypatch, advertised, expected):
    calls = []
    tokenizer = SimpleNamespace(
        model_max_length=advertised,
        apply_chat_template=lambda *args, **kwargs: [1] * 8000,
    )

    def load_tokenizer_stub(repo, *, revision):
        calls.append((repo, revision))
        return tokenizer

    def load_config_stub(repo, *, revision):
        calls.append((repo, revision))
        return SimpleNamespace(max_position_embeddings=8192)

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            AutoTokenizer=SimpleNamespace(from_pretrained=load_tokenizer_stub),
            AutoConfig=SimpleNamespace(from_pretrained=load_config_stub),
        ),
    )
    config = cfg.load()
    actual = load_tokenizer(config)
    assert actual.model_max_length == expected
    spec = config["models"]["generator"]
    assert calls == [(spec["repo_id"], spec["revision"])] * 2
    report = preflight_generation([{"id": "too-long", "messages": []}], actual, config)
    assert not report["passed"]
    assert report["context_limit"] == expected
    assert report["over_context"][0]["requested_tokens"] == 8512
