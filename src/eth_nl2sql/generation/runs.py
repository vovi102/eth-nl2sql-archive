"""Experiment configurations and their rendered prompt/training files.

Prompts are rendered locally (linking and retrieval need the dictionary and the
encoder); the GPU side only reads the messages and generates.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from eth_nl2sql.generation.prompt import build_messages, messages_digest, system_prompt
from eth_nl2sql.linking.context import Linking, render
from eth_nl2sql.linking.variants import EXPERIMENTS


@dataclass(frozen=True)
class RunConfig:
    name: str
    examples: bool  # five retrieved training examples (B2)
    linking: bool  # linking hints in the prompt
    fine_tuned: bool  # whether to load a QLoRA adapter
    prompt_style: str = "catalog"
    linking_variant: str = "full"

    def __post_init__(self) -> None:
        if self.prompt_style not in ("catalog", "compact"):
            raise ValueError(f"Unknown prompt style: {self.prompt_style}")


CONFIGS = {
    config.name: config
    for config in (
        RunConfig("b1", examples=False, linking=False, fine_tuned=False),
        RunConfig("b1l", examples=False, linking=True, fine_tuned=False),
        RunConfig("b2", examples=True, linking=False, fine_tuned=False),
        RunConfig("b2l", examples=True, linking=True, fine_tuned=False),
        RunConfig("b3-base", False, False, False, prompt_style="compact"),
        RunConfig("b3l-base", False, True, False, prompt_style="compact"),
        RunConfig("b3", False, False, True, prompt_style="compact"),
        RunConfig("b3l", False, True, True, prompt_style="compact"),
    )
}
CONFIGS.update(
    {
        name: RunConfig(
            name, examples=True, linking=True, fine_tuned=False, linking_variant=variant
        )
        for name, variant in EXPERIMENTS.items()
    }
)


def _messages(
    config: RunConfig,
    question: str,
    *,
    system: str,
    linking: Linking | None,
    examples: Sequence[Mapping],
) -> list[dict]:
    if config.linking and linking is not None and linking.variant != config.linking_variant:
        raise ValueError(f"{config.name} requires linking variant {config.linking_variant}")
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
    system = system_prompt(catalog, compact=config.prompt_style == "compact")
    rows = []
    for case in cases:
        safe_case = {key: case[key] for key in ("id", "question", "family_id") if key in case}
        examples = retrieve(safe_case) if config.examples else ()
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


def prompt_suite(
    cases: Sequence[Mapping],
    *,
    catalog: Mapping,
    linkings: Mapping[str, Mapping[str, Linking]],
    retrieve: Callable[[Mapping], Sequence[Mapping]],
) -> dict[str, list[dict]]:
    """Retrieve once per question, then hold examples fixed for the entire comparison."""
    examples = {
        case["id"]: tuple(
            retrieve({k: case[k] for k in ("id", "question", "family_id") if k in case})
        )
        for case in cases
    }
    return {
        name: prompt_rows(
            CONFIGS[name],
            cases,
            catalog=catalog,
            linkings=linkings[EXPERIMENTS[name]] if name in EXPERIMENTS else None,
            retrieve=lambda case: examples[case["id"]],
        )
        for name in ("b2", *EXPERIMENTS)
    }


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
    system = system_prompt(catalog, compact=config.prompt_style == "compact")
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
