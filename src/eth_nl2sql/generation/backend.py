"""Pinned 4-bit generation with preflight and verified, appendable predictions."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from pathlib import Path

from eth_nl2sql.config import read_jsonl, sha256_file, write_json
from eth_nl2sql.experiments import (
    ResourceMonitor,
    checked_rows,
    digest,
    generation_provenance,
    prediction_manifest,
    verify_predictions,
    write_manifest,
)


def load_tokenizer(config: Mapping):
    from transformers import AutoTokenizer

    spec = config["models"]["generator"]
    return AutoTokenizer.from_pretrained(spec["repo_id"], revision=spec["revision"])


def load_generator(config: Mapping, *, adapter: Path | None = None, tokenizer=None):
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig

    spec = config["models"]["generator"]
    tokenizer = tokenizer if tokenizer is not None else load_tokenizer(config)
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.float16,
    )
    model = AutoModelForCausalLM.from_pretrained(
        spec["repo_id"],
        revision=spec["revision"],
        device_map="auto",
        torch_dtype=torch.float16,
        quantization_config=quantization,
    )
    if adapter is not None:
        from peft import PeftModel

        model = PeftModel.from_pretrained(model, str(adapter))
    model.eval()
    return model, tokenizer


def stop_token_ids(tokenizer) -> list[int]:
    """Llama-3 ends an assistant turn with <|eot_id|>, not only the EOS token."""
    ids = [tokenizer.eos_token_id]
    eot = tokenizer.convert_tokens_to_ids("<|eot_id|>")
    if isinstance(eot, int) and eot not in ids and eot != tokenizer.unk_token_id:
        ids.append(eot)
    return ids


def preflight_generation(prompts: list[dict], tokenizer, config: Mapping) -> dict:
    started = time.perf_counter()
    maximum = config["generation"]["max_new_tokens"]
    if maximum <= 0:
        raise ValueError("generation.max_new_tokens must be positive")
    context = tokenizer.model_max_length
    lengths, errors = [], []
    for row in prompts:
        length = len(tokenizer.apply_chat_template(row["messages"], add_generation_prompt=True))
        lengths.append(length)
        if length + maximum > context:
            errors.append(
                {"id": row["id"], "input_tokens": length, "requested_tokens": length + maximum}
            )
    return {
        "passed": not errors,
        "input_rows": len(prompts),
        "kept_rows": len(prompts) - len(errors),
        "over_context": errors,
        "dropped_rows": 0,
        "truncation": False,
        "input_tokens": sum(lengths),
        "min_input_tokens": min(lengths),
        "max_input_tokens": max(lengths),
        "max_new_tokens": maximum,
        "context_limit": context,
        "runtime_s": time.perf_counter() - started,
    }


class HuggingFaceGenerationBackend:
    def seed(self, seed: int) -> None:
        from transformers import set_seed

        set_seed(seed)

    def tokenizer(self, config: Mapping):
        return load_tokenizer(config)

    def monitor(self):
        return ResourceMonitor()

    def load(self, config, adapter, tokenizer):
        return load_generator(config, adapter=adapter, tokenizer=tokenizer)[0]

    def generate(self, model, tokenizer, row: Mapping, config: Mapping) -> dict:
        import torch

        generation = config["generation"]
        # Decoding seed stays fixed across training seeds.
        self.seed(generation["seed"])
        inputs = tokenizer.apply_chat_template(
            row["messages"], add_generation_prompt=True, return_tensors="pt"
        ).to(model.device)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        started = time.perf_counter()
        with torch.inference_mode():
            output = model.generate(
                inputs,
                attention_mask=torch.ones_like(inputs),
                max_new_tokens=generation["max_new_tokens"],
                do_sample=generation["do_sample"],
                eos_token_id=stop_token_ids(tokenizer),
                pad_token_id=tokenizer.eos_token_id,
            )
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        elapsed = (time.perf_counter() - started) * 1000.0
        new_tokens = output[0][inputs.shape[-1] :]
        stopped = int(new_tokens[-1]) in stop_token_ids(tokenizer) if len(new_tokens) else False
        return {
            "raw_output": tokenizer.decode(new_tokens, skip_special_tokens=True),
            "latency_ms": elapsed,
            "input_tokens": int(inputs.shape[-1]),
            "output_tokens": int(new_tokens.shape[-1]),
            "finish_reason": "stop" if stopped else "length",
        }


def generate_file(
    prompts_path: Path,
    out_path: Path,
    config: Mapping,
    *,
    adapter: Path | None = None,
    limit: int | None = None,
    name: str | None = None,
    seed: int = 42,
    backend=None,
) -> int:
    prompts = checked_rows(prompts_path)
    name = name or prompts[0]["config"]
    if any(row.get("config") != name for row in prompts):
        raise ValueError(f"Mixed or wrong prompt configuration: {prompts_path}")
    if limit is not None and limit <= 0:
        raise ValueError("--limit must be positive")
    provenance = generation_provenance(prompts_path, config, name, seed, adapter)
    manifest_path = prediction_manifest(out_path)
    previous = {}
    if out_path.exists() or manifest_path.exists():
        previous = verify_predictions(out_path, prompts, provenance)
    done = {row["id"] for row in read_jsonl(out_path)} if out_path.exists() else set()
    pending = [row for row in prompts[:limit] if row["id"] not in done]
    # Always check provenance, even when an existing run has nothing left to do.
    if not pending:
        if previous.get("status") != "complete" and len(done) == len(prompts):
            # A process can stop after its last append and before its final manifest.
            # Valid record checksums let us finalize without loading the model again.
            outputs = read_jsonl(out_path)
            write_manifest(
                manifest_path,
                provenance,
                status="complete",
                predictions_sha256=sha256_file(out_path),
                sessions=previous.get("sessions", []),
                preflight=previous.get("preflight"),
                recovered_after_interruption=True,
                resource_measurements_complete=False,
                **generation_totals(outputs, len(prompts)),
            )
        return 0
    backend = backend or HuggingFaceGenerationBackend()
    backend.seed(config["generation"]["seed"])
    monitor = backend.monitor()
    tokenizer = backend.tokenizer(config)
    preflight = preflight_generation(prompts, tokenizer, config)
    write_json(out_path.with_name(f"preflight-{out_path.stem}.json"), preflight)
    if not preflight["passed"]:
        raise ValueError("Generation inputs exceed the model context; no prompts were truncated")
    # Mark running before appending; each record is also individually checksummed,
    # allowing an interrupted append-only file to be validated without a final hash.
    sessions = list(previous.get("sessions", []))
    write_manifest(
        manifest_path, provenance, status="running", sessions=sessions, preflight=preflight
    )
    try:
        model = backend.load(config, adapter, tokenizer)
        with out_path.open("a") as handle:
            for row in pending:
                result = backend.generate(model, tokenizer, row, config)
                record = {
                    **result,
                    "id": row["id"],
                    "config": name,
                    "seed": seed,
                    "prompt_sha256": row["prompt_sha256"],
                    "provenance_sha256": digest(provenance),
                }
                record["record_sha256"] = digest(record)
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                handle.flush()
    except Exception as exc:
        recovered = read_jsonl(out_path) if out_path.exists() else []
        sessions.append(
            {
                "status": "interrupted",
                "generated_rows": len(recovered) - len(done),
                "error": f"{type(exc).__name__}: {exc}",
                **monitor.summary(),
            }
        )
        write_manifest(
            manifest_path,
            provenance,
            status="interrupted",
            sessions=sessions,
            preflight=preflight,
            predictions_sha256=sha256_file(out_path) if out_path.exists() else None,
        )
        raise
    sessions.append({"generated_rows": len(pending), **monitor.summary()})
    outputs = read_jsonl(out_path)
    write_manifest(
        manifest_path,
        provenance,
        status="complete" if len(outputs) == len(prompts) else "partial",
        predictions_sha256=sha256_file(out_path),
        sessions=sessions,
        **generation_totals(outputs, len(prompts)),
        preflight=preflight,
    )
    return len(pending)


def generation_totals(outputs: list[dict], expected: int) -> dict:
    return {
        "input_tokens": sum(r["input_tokens"] for r in outputs),
        "output_tokens": sum(r["output_tokens"] for r in outputs),
        "length_limited_rows": sum(r.get("finish_reason") == "length" for r in outputs),
        "generated_rows": len(outputs),
        "expected_rows": expected,
    }
