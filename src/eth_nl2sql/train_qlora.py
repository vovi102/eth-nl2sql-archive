"""QLoRA fine-tuning for B3 (runs on a Kaggle T4; requires the `gpu` extra).

Each training row holds the exact inference prompt and the gold SQL. The loss is
computed on the SQL tokens only; prompt tokens are masked with -100 (as in
luanvan `models/b3/formatting.py`). Rows longer than `max_length` are dropped
and counted rather than truncated.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from pathlib import Path

from eth_nl2sql.config import read_jsonl
from eth_nl2sql.generation.backend import stop_token_ids


def encode_row(tokenizer, row: Mapping, max_length: int) -> dict | None:
    prompt = tokenizer.apply_chat_template(row["messages"], add_generation_prompt=True)
    eot = stop_token_ids(tokenizer)[-1]
    target = tokenizer(row["target"], add_special_tokens=False)["input_ids"] + [eot]
    input_ids = list(prompt) + target
    if len(input_ids) > max_length:
        return None
    return {
        "input_ids": input_ids,
        "attention_mask": [1] * len(input_ids),
        "labels": [-100] * len(prompt) + target,
    }


class PaddingCollator:
    def __init__(self, pad_id: int) -> None:
        self.pad_id = pad_id

    def __call__(self, features: list[dict]) -> dict:
        import torch

        width = max(len(feature["input_ids"]) for feature in features)

        def padded(key: str, value: int) -> torch.Tensor:
            return torch.tensor(
                [f[key] + [value] * (width - len(f[key])) for f in features], dtype=torch.long
            )

        return {
            "input_ids": padded("input_ids", self.pad_id),
            "attention_mask": padded("attention_mask", 0),
            "labels": padded("labels", -100),
        }


def train(train_path: Path, dev_path: Path, out_dir: Path, config: Mapping) -> dict:
    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import EarlyStoppingCallback, Trainer, TrainingArguments

    from eth_nl2sql.generation.backend import load_generator

    settings = config["qlora"]
    model, tokenizer = load_generator(config)
    tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)
    model = get_peft_model(
        model,
        LoraConfig(
            r=settings["r"],
            lora_alpha=settings["alpha"],
            lora_dropout=settings["dropout"],
            target_modules=list(settings["target_modules"]),
            bias="none",
            task_type="CAUSAL_LM",
        ),
    )

    def encoded(path: Path) -> tuple[list[dict], int]:
        rows = [encode_row(tokenizer, row, settings["max_length"]) for row in read_jsonl(path)]
        kept = [row for row in rows if row is not None]
        return kept, len(rows) - len(kept)

    train_rows, train_dropped = encoded(train_path)
    dev_rows, dev_dropped = encoded(dev_path)
    batch = settings["per_device_batch_size"] * settings["gradient_accumulation_steps"]
    steps_per_epoch = math.ceil(len(train_rows) / batch)
    eval_steps = max(1, steps_per_epoch // 2)
    arguments = TrainingArguments(
        output_dir=str(out_dir / "checkpoints"),
        per_device_train_batch_size=settings["per_device_batch_size"],
        per_device_eval_batch_size=settings["per_device_batch_size"],
        gradient_accumulation_steps=settings["gradient_accumulation_steps"],
        learning_rate=settings["learning_rate"],
        lr_scheduler_type=settings["lr_scheduler"],
        warmup_ratio=0.03,
        num_train_epochs=settings["max_epochs"],
        eval_strategy="steps",
        eval_steps=eval_steps,
        save_strategy="steps",
        save_steps=eval_steps,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        logging_steps=10,
        fp16=True,
        gradient_checkpointing=True,
        report_to=[],
        seed=config["generation"]["seed"],
    )
    trainer = Trainer(
        model=model,
        args=arguments,
        train_dataset=train_rows,
        eval_dataset=dev_rows,
        data_collator=PaddingCollator(tokenizer.pad_token_id),
        callbacks=[
            EarlyStoppingCallback(early_stopping_patience=settings["early_stopping_patience"])
        ],
    )
    output = trainer.train()
    adapter_dir = out_dir / "adapter"
    model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))
    summary = {
        "train_rows": len(train_rows),
        "train_dropped_over_max_length": train_dropped,
        "dev_rows": len(dev_rows),
        "dev_dropped_over_max_length": dev_dropped,
        "steps": output.global_step,
        "train_runtime_s": output.metrics.get("train_runtime"),
        "best_eval_loss": trainer.state.best_metric,
        "peak_gpu_memory_gib": torch.cuda.max_memory_allocated() / 2**30
        if torch.cuda.is_available()
        else None,
        "log_history": trainer.state.log_history,
    }
    (out_dir / "training-summary.json").write_text(json.dumps(summary, indent=2))
    return summary
