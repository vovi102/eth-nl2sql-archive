"""Experiment configurations and their rendered prompt/training files.

Prompts are rendered locally (linking and retrieval need the dictionary and the
encoder); the GPU side only reads the messages and generates.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from eth_nl2sql.generation.prompt import build_messages, messages_digest, system_prompt
from eth_nl2sql.linking.context import Linking, render


@dataclass(frozen=True)
class RunConfig:
    name: str
    examples: bool  # five retrieved training examples (B2)
    linking: bool  # linking hints in the prompt
    fine_tuned: bool  # QLoRA adapter + compact schema prompt (B3)


CONFIGS = {
    config.name: config
    for config in (
        RunConfig("b1", examples=False, linking=False, fine_tuned=False),
        RunConfig("b1l", examples=False, linking=True, fine_tuned=False),
        RunConfig("b2", examples=True, linking=False, fine_tuned=False),
        RunConfig("b2l", examples=True, linking=True, fine_tuned=False),
        RunConfig("b3", examples=False, linking=False, fine_tuned=True),
        RunConfig("b3l", examples=False, linking=True, fine_tuned=True),
    )
}


def _messages(
    config: RunConfig,
    question: str,
    *,
    system: str,
    linking: Linking | None,
    examples: Sequence[Mapping],
) -> list[dict]:
    hints = render(linking) if config.linking and linking is not None else None
    if config.linking and linking is None:
        raise ValueError(f"{config.name} needs linking results for every question")
    return build_messages(question, system=system, examples=examples, linking=hints)


def prompt_rows(
    config: RunConfig,
    cases: Sequence[Mapping],
    *,
    catalog: Mapping,
    linkings: Mapping[str, Linking] | None = None,
    retrieve: Callable[[Mapping], Sequence[Mapping]] | None = None,
) -> list[dict]:
    system = system_prompt(catalog, compact=config.fine_tuned)
    rows = []
    for case in cases:
        examples = retrieve(case) if config.examples else ()
        if config.examples and len(examples) != 5:
            raise ValueError("B2 prompts need exactly five examples")
        messages = _messages(
            config,
            case["question"],
            system=system,
            linking=(linkings or {}).get(case["id"]),
            examples=examples,
        )
        rows.append(
            {
                "id": case["id"],
                "config": config.name,
                "messages": messages,
                "prompt_sha256": messages_digest(messages),
                "example_ids": [example["id"] for example in examples],
            }
        )
    return rows


def training_rows(
    config: RunConfig,
    records: Sequence[Mapping],
    *,
    catalog: Mapping,
    linkings: Mapping[str, Linking] | None = None,
) -> list[dict]:
    """Supervised rows for QLoRA: the inference prompt plus the gold SQL as target."""
    if not config.fine_tuned:
        raise ValueError("training rows are only defined for fine-tuned configurations")
    system = system_prompt(catalog, compact=True)
    return [
        {
            "id": record["id"],
            "messages": _messages(
                config,
                record["question"],
                system=system,
                linking=(linkings or {}).get(record["id"]),
                examples=(),
            ),
            "target": record["sql"],
        }
        for record in records
    ]
