"""QLoRA with SQL-only loss, explicit preflight and isolated training seeds."""

from __future__ import annotations

import json
import math
import time
from collections.abc import Mapping
from pathlib import Path

from eth_nl2sql.config import sha256_file, write_json
from eth_nl2sql.experiments import (
    ResourceMonitor,
    check_manifest,
    checked_rows,
    training_provenance,
    tree_digest,
    write_manifest,
)
from eth_nl2sql.generation.backend import load_generator, load_tokenizer, stop_token_ids


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


def encode_split(tokenizer, rows: list[dict], max_length: int) -> tuple[list[dict], dict]:
    encoded, lengths, dropped = [], [], []
    prompt_tokens = target_tokens = kept_tokens = 0
    for row in rows:
        # Encode without truncation, including the complete SQL and turn terminator.
        full = encode_row(tokenizer, row, max_length=math.inf)
        length = len(full["input_ids"])
        lengths.append(length)
        prompt_tokens += full["labels"].count(-100)
        target_tokens += sum(label != -100 for label in full["labels"])
        if length > max_length:
            dropped.append({"id": row["id"], "tokens": length})
        else:
            encoded.append(full)
            kept_tokens += length
    return encoded, {
        "input_rows": len(rows),
        "kept_rows": len(encoded),
        "dropped_over_max_length": len(dropped),
        "dropped_fraction": len(dropped) / len(rows),
        "kept_ids": [
            row["id"] for row, length in zip(rows, lengths, strict=True) if length <= max_length
        ],
        "dropped": dropped,
        "prompt_tokens": prompt_tokens,
        "target_tokens_including_eot": target_tokens,
        "total_tokens": sum(lengths),
        "kept_tokens": kept_tokens,
        "dropped_tokens": sum(lengths) - kept_tokens,
        "min_tokens": min(lengths),
        "max_tokens": max(lengths),
    }


def training_inputs(train_path: Path, dev_path: Path, config: Mapping) -> tuple[list, list]:
    settings = config["qlora"]
    for key in (
        "max_length",
        "per_device_batch_size",
        "gradient_accumulation_steps",
        "max_epochs",
        "learning_rate",
        "r",
        "alpha",
        "early_stopping_patience",
    ):
        if settings[key] <= 0:
            raise ValueError(f"qlora.{key} must be positive")
    if not settings["target_modules"] or not 0 <= settings["dropout"] < 1:
        raise ValueError("Invalid LoRA target_modules/dropout")
    train_rows = checked_rows(train_path, training=True)
    dev_rows = checked_rows(dev_path, training=True)
    if {row["id"] for row in train_rows} & {row["id"] for row in dev_rows}:
        raise ValueError("Train/dev contain overlapping IDs")
    return train_rows, dev_rows


def preflight_training(
    train_path: Path,
    dev_path: Path,
    config: Mapping,
    *,
    tokenizer,
    out: Path | None = None,
) -> tuple[list[dict], list[dict], dict]:
    started = time.perf_counter()
    train_rows, dev_rows = training_inputs(train_path, dev_path, config)
    max_length = config["qlora"]["max_length"]
    if max_length > tokenizer.model_max_length:
        raise ValueError("qlora.max_length exceeds the tokenizer model context")
    train_encoded, train_stats = encode_split(tokenizer, train_rows, max_length)
    dev_encoded, dev_stats = encode_split(tokenizer, dev_rows, max_length)
    errors = [
        f"{name} has no rows after max_length filtering"
        for name, rows in (("train", train_encoded), ("dev", dev_encoded))
        if not rows
    ]
    report = {
        "passed": not errors,
        "errors": errors,
        "max_length": max_length,
        "context_limit": tokenizer.model_max_length,
        "train": train_stats,
        "dev": dev_stats,
        "runtime_s": time.perf_counter() - started,
        "truncation": False,
    }
    if out is not None:
        write_json(out, report)
    if errors:
        raise ValueError("; ".join(errors))
    return train_encoded, dev_encoded, report


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


class HuggingFaceTrainingBackend:
    """Optional GPU dependencies stay behind this boundary for offline fixture tests."""

    def seed(self, seed: int) -> None:
        from transformers import set_seed

        # Covers Python, NumPy, torch and CUDA before any model/adapter is created.
        set_seed(seed)

    def tokenizer(self, config: Mapping):
        return load_tokenizer(config)

    def monitor(self):
        return ResourceMonitor()

    def fit(self, train_rows, dev_rows, tokenizer, out_dir, config, seed, resume, provenance):
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from transformers import EarlyStoppingCallback, Trainer, TrainerCallback, TrainingArguments

        settings = config["qlora"]
        model, _ = load_generator(config, tokenizer=tokenizer)
        model.config.use_cache = False
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
            seed=seed,
            data_seed=seed,
        )

        class CheckpointProvenance(TrainerCallback):
            def on_train_begin(self, args, state, control, **kwargs):
                if state.best_model_checkpoint:
                    # Trainer state stores an absolute path on the original host.
                    # Resolve the verified checkpoint under this run after copying it.
                    best = Path(args.output_dir) / Path(state.best_model_checkpoint).name
                    if not best.is_dir():
                        raise ValueError(f"Missing best dev checkpoint: {best}")
                    state.best_model_checkpoint = str(best)

            def on_save(self, args, state, control, **kwargs):
                checkpoint = Path(args.output_dir) / f"checkpoint-{state.global_step}"
                write_manifest(
                    checkpoint / "checkpoint-manifest.json",
                    provenance,
                    checkpoint_sha256=tree_digest(checkpoint, exclude="checkpoint-manifest.json"),
                )

        tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
        trainer = Trainer(
            model=model,
            args=arguments,
            train_dataset=train_rows,
            eval_dataset=dev_rows,
            data_collator=PaddingCollator(tokenizer.pad_token_id),
            callbacks=[
                EarlyStoppingCallback(early_stopping_patience=settings["early_stopping_patience"]),
                CheckpointProvenance(),
            ],
        )
        output = trainer.train(resume_from_checkpoint=str(resume) if resume else None)
        adapter_dir = out_dir / "adapter"
        model.save_pretrained(str(adapter_dir))
        tokenizer.save_pretrained(str(adapter_dir))
        return {
            "steps": output.global_step,
            "train_runtime_s": output.metrics.get("train_runtime"),
            "best_eval_loss": trainer.state.best_metric,
            # Store a relative path so artifacts remain portable.
            "best_checkpoint": str(Path(trainer.state.best_model_checkpoint).relative_to(out_dir)),
            "checkpoint_selection": "minimum dev eval_loss",
            "log_history": trainer.state.log_history,
        }


def resume_checkpoint(out_dir: Path, provenance: Mapping) -> Path:
    candidates = sorted(
        (
            p
            for p in (out_dir / "checkpoints").glob("checkpoint-*")
            if p.is_dir() and p.name.removeprefix("checkpoint-").isdigit()
        ),
        key=lambda p: int(p.name.removeprefix("checkpoint-")),
    )
    if not candidates:
        raise ValueError(f"No checkpoint to resume in {out_dir}")
    # Verify all retained checkpoints: Trainer may reload an earlier best checkpoint.
    for checkpoint in candidates:
        manifest = check_manifest(checkpoint / "checkpoint-manifest.json", provenance)
        if manifest.get("checkpoint_sha256") != tree_digest(
            checkpoint, exclude="checkpoint-manifest.json"
        ):
            raise ValueError(f"Checkpoint hash mismatch: {checkpoint}")
    return candidates[-1]


def train(
    train_path: Path,
    dev_path: Path,
    out_dir: Path,
    config: Mapping,
    *,
    name: str = "b3",
    seed: int = 42,
    resume: bool = False,
    backend=None,
) -> dict:
    # Validate files/settings/provenance before importing GPU dependencies.
    training_inputs(train_path, dev_path, config)
    provenance = training_provenance(train_path, dev_path, config, name, seed)
    manifest_path = out_dir / "training-manifest.json"
    checkpoint = None
    if manifest_path.exists():
        manifest = check_manifest(manifest_path, provenance)
        if not resume:
            raise ValueError(f"Training artifacts already exist: {out_dir}; use --resume")
        if manifest.get("status") == "complete":
            if manifest.get("adapter_sha256") != tree_digest(out_dir / "adapter"):
                raise ValueError(f"Adapter hash mismatch: {out_dir}")
            summary_path = out_dir / "training-summary.json"
            if manifest.get("summary_sha256") != sha256_file(summary_path):
                raise ValueError(f"Training summary hash mismatch: {out_dir}")
            return json.loads(summary_path.read_text())
        if (out_dir / "checkpoints").exists():
            checkpoint = resume_checkpoint(out_dir, provenance)
        elif (out_dir / "adapter").exists():
            raise ValueError(f"Incomplete adapter without a checkpoint: {out_dir}")
    elif (out_dir / "adapter").exists() or (out_dir / "checkpoints").exists():
        raise ValueError(f"Unverified training artifacts: {out_dir}")

    backend = backend or HuggingFaceTrainingBackend()
    backend.seed(seed)
    monitor = backend.monitor()
    tokenizer = backend.tokenizer(config)
    train_rows, dev_rows, preflight = preflight_training(
        train_path, dev_path, config, tokenizer=tokenizer, out=out_dir / "preflight-training.json"
    )
    write_manifest(manifest_path, provenance, status="running")
    try:
        result = backend.fit(
            train_rows, dev_rows, tokenizer, out_dir, config, seed, checkpoint, provenance
        )
    except Exception as exc:
        write_manifest(
            manifest_path,
            provenance,
            status="interrupted",
            preflight=preflight,
            resources=monitor.summary(),
            error=f"{type(exc).__name__}: {exc}",
        )
        raise
    summary = {
        "config": name,
        "seed": seed,
        "preflight": preflight,
        "train_rows": len(train_rows),
        "dev_rows": len(dev_rows),
        "train_dropped_over_max_length": preflight["train"]["dropped_over_max_length"],
        "dev_dropped_over_max_length": preflight["dev"]["dropped_over_max_length"],
        **result,
        **monitor.summary(),
    }
    summary_path = out_dir / "training-summary.json"
    write_json(summary_path, summary)
    write_manifest(
        manifest_path,
        provenance,
        status="complete",
        adapter_sha256=tree_digest(out_dir / "adapter"),
        summary_sha256=sha256_file(summary_path),
    )
    return summary
