"""Greedy generation with the pinned 4-bit Llama-3 model (runs on a Kaggle T4).

Requires the `gpu` extra. Output is appended per question, so a stopped session
resumes where it left off.
"""

from __future__ import annotations

import json
import time
from collections.abc import Mapping
from pathlib import Path

from eth_nl2sql.config import read_jsonl


def load_generator(config: Mapping, *, adapter: Path | None = None):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    spec = config["models"]["generator"]
    tokenizer = AutoTokenizer.from_pretrained(spec["repo_id"], revision=spec["revision"])
    # T4 has no bfloat16 support, so compute in float16.
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


def generate_file(
    prompts_path: Path,
    out_path: Path,
    config: Mapping,
    *,
    adapter: Path | None = None,
    limit: int | None = None,
) -> int:
    import torch

    prompts = read_jsonl(prompts_path)[:limit]
    done = {row["id"] for row in read_jsonl(out_path)} if out_path.exists() else set()
    pending = [row for row in prompts if row["id"] not in done]
    if not pending:
        return 0
    model, tokenizer = load_generator(config, adapter=adapter)
    generation = config["generation"]
    stops = stop_token_ids(tokenizer)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as handle:
        for row in pending:
            torch.manual_seed(generation["seed"])
            inputs = tokenizer.apply_chat_template(
                row["messages"], add_generation_prompt=True, return_tensors="pt"
            ).to(model.device)
            started = time.perf_counter()
            with torch.inference_mode():
                output = model.generate(
                    inputs,
                    attention_mask=torch.ones_like(inputs),
                    max_new_tokens=generation["max_new_tokens"],
                    do_sample=generation["do_sample"],
                    eos_token_id=stops,
                    pad_token_id=tokenizer.eos_token_id,
                )
            latency_ms = (time.perf_counter() - started) * 1000.0
            new_tokens = output[0][inputs.shape[-1] :]
            record = {
                "id": row["id"],
                "config": row["config"],
                "prompt_sha256": row["prompt_sha256"],
                "raw_output": tokenizer.decode(new_tokens, skip_special_tokens=True),
                "latency_ms": latency_ms,
                "input_tokens": int(inputs.shape[-1]),
                "output_tokens": int(new_tokens.shape[-1]),
            }
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            handle.flush()
    return len(pending)
