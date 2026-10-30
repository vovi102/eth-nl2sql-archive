"""Frozen-adapter T11B diagnosis; isolated prompts, paired probes and smoke gates.

No test-v2 content, new training, SQL repair, or overwrite of original run outputs.
The 2x2 prompt intervention is declared before generation. Its combined candidate
can continue to 100 development questions only after all ten compile unchanged.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import time
import zipfile
from collections import Counter
from datetime import date
from pathlib import Path

from eth_nl2sql import config as cfg
from eth_nl2sql.experiments import ResourceMonitor, tree_digest
from eth_nl2sql.generation.backend import HuggingFaceGenerationBackend, stop_token_ids
from eth_nl2sql.generation.prompt import messages_digest
from eth_nl2sql.generation.smoke import inspect_predictions

ROOT = cfg.ROOT
REPORT = ROOT / "reports/gpu-development-t11b"
WORK = REPORT / "diagnosis"
ORIGINAL = ROOT / "runs/b3/seed-42"
DATE_RE = re.compile(r"DATE '([0-9]{4}-[0-9]{2}-[0-9]{2})'")
VARIANTS = ("original", "dates", "columns", "dates-columns")
DATE_RULES = (
    "\nDATE SEMANTICS: All date intervals are half-open [start_date, end_date). "
    "Convert natural-language inclusive final dates to the next calendar day for end_date. "
    "For example, the first three days of a month means day 1 through day 3 inclusive, "
    "with end_date on day 4. An explicitly exclusive end date stays unchanged. "
    "Always call date-parameterized relations with DATE literals."
)


def original_output_manifest() -> dict:
    with zipfile.ZipFile(REPORT / "b3-seed-42/artifacts.zip") as archive:
        return json.loads(
            archive.read("reports/gpu-development-t11b/b3-seed-42/outputs-manifest.json")
        )


def variant_messages(messages: list[dict], variant: str, catalog: dict) -> list[dict]:
    """Same additions for the frozen adapter and b3-base; never inspect gold SQL."""
    if variant not in VARIANTS:
        raise ValueError(f"Unknown prompt intervention: {variant}")
    result = copy.deepcopy(messages)
    if "columns" in variant:
        fields = "\n".join(
            f"{name}: " + ", ".join(sorted(relation["fields"]))
            for name, relation in sorted(catalog["analytical_relations"].items())
        )
        result[0]["content"] += (
            "\nAVAILABLE COLUMNS (use only columns of the selected relation):\n" + fields
        )
    if "dates" in variant:
        result[0]["content"] += DATE_RULES
    return result


def audit() -> None:
    """Rebuild an evidence ledger from original files without changing them."""
    from t11a import test_hashes
    from t11b_continue import review

    WORK.mkdir(parents=True, exist_ok=True)
    original = cfg.read_jsonl(ORIGINAL / "predictions-dev_eval.jsonl")
    cases = {r["id"]: r for r in cfg.read_jsonl(REPORT / "b3-seed-42/cases.jsonl")}
    gold = {r["id"]: r for r in cfg.read_jsonl(ROOT / "data/dev_eval.jsonl")}
    errors = []
    for row in original:
        case, reference = cases[row["id"]], gold[row["id"]]
        sql = case["predicted_sql"] or ""
        predicted_dates, gold_dates = DATE_RE.findall(sql), DATE_RE.findall(reference["sql"])
        categories = []
        if predicted_dates != gold_dates:
            categories.append("date_window")
        if case["status"] == "compile_error":
            categories.append("unknown_column")
        if "labeled_token_transfers`" in sql and "token_transfer_facts`" in reference["sql"]:
            categories.append("different_relation")
        if row["id"] == "t35-008":
            categories.append("extra_positive_amount_filter")
        if row["id"] == "t35-004":
            categories.append("missing_coalesce_and_alias")
        errors.append(
            dict(
                id=row["id"],
                question=reference["question"],
                gold_sql=reference["sql"],
                predicted_sql=sql,
                predicted_dates=predicted_dates,
                gold_dates=gold_dates,
                status=case["status"],
                execution_match=case["execution_match"],
                error_categories=categories,
                error=case["error"],
            )
        )
    cfg.write_jsonl(WORK / "original-errors.jsonl", errors)
    datasets = {s: cfg.read_jsonl(ROOT / f"data/{s}.jsonl") for s in ("train", "dev", "dev_eval")}
    distributions = {}
    for split, rows in datasets.items():
        distributions[split] = {
            "rows": len(rows),
            "questions_with_iso_date": sum(
                bool(re.search(r"\d{4}-\d\d-\d\d", r["question"])) for r in rows
            ),
            "questions_with_natural_month": sum(
                bool(re.search(r"\bJune\b", r["question"], re.I)) for r in rows
            ),
            "template_ids": sorted({r["template_id"] for r in rows if "template_id" in r}),
            "bad_column_targets": {
                c: sum(c in r["sql"] for r in rows)
                for c in ("is_successfull", "block_transaction_count")
            },
        }
    overlaps = {
        key: len({r[key] for r in datasets["train"]} & {r[key] for r in datasets["dev"]})
        for key in ("id", "family_id", "question", "sql", "template_id")
    }
    archive = REPORT / "b3-seed-42/artifacts.zip"
    manifest = original_output_manifest()
    for path, expected in manifest.items():
        if cfg.sha256_file(ROOT / path) != expected:
            raise ValueError(f"Original output changed: {path}")
    ledger = {
        "evaluation_role": "development",
        "scope": "first ten dev_eval cases",
        "archive_sha256": cfg.sha256_file(archive),
        "verified_original_files": len(manifest),
        "adapter_sha256": tree_digest(ORIGINAL / "adapter"),
        "predictions_sha256": cfg.sha256_file(ORIGINAL / "predictions-dev_eval.jsonl"),
        "error_counts_nonexclusive": dict(
            Counter(c for r in errors for c in r["error_categories"])
        ),
        "datasets": distributions,
        "train_dev_overlaps": overlaps,
        "test_v2_hashes_only": test_hashes(),
    }
    cfg.write_json(WORK / "evidence.json", ledger)
    result = review("b3-seed-42")
    cfg.write_json(REPORT / "b3-seed-42/review.json", result)
    state_path = REPORT / "continuation.json"
    state = json.loads(state_path.read_text())
    state["jobs"]["b3-seed-42"].update(
        status="evaluated", review=result, remote_status="KernelWorkerStatus.COMPLETE"
    )
    state.update(status="stopped_for_diagnosis", current_job="b3-seed-42")
    cfg.write_json(state_path, state)
    print(
        json.dumps(
            {"original_review": result["decision"], "errors": ledger["error_counts_nonexclusive"]}
        )
    )


def prepare(archive: Path, *, attempt: int = 1) -> None:
    """Questions only for dev_eval; held-out synthetic dev targets for loss probes."""
    WORK.mkdir(parents=True, exist_ok=True)
    catalog = json.loads(cfg.CATALOG_PATH.read_text())
    inputs = cfg.read_jsonl(ROOT / "runs/b3/prompts-dev_eval.jsonl")
    prompts = []
    for variant in VARIANTS:
        for row in inputs:
            messages = variant_messages(row["messages"], variant, catalog)
            prompts.append(
                {
                    "id": row["id"],
                    "variant": variant,
                    "messages": messages,
                    "prompt_sha256": messages_digest(messages),
                }
            )
    cfg.write_jsonl(WORK / "prompts.jsonl", prompts)
    dev = {r["id"]: r for r in cfg.read_jsonl(ROOT / "data/dev.jsonl")}
    probes, templates = [], set()
    for row in cfg.read_jsonl(ROOT / "runs/b3/sft-dev.jsonl"):
        record = dev[row["id"]]
        if record["style"] != "formal" or record["template_id"] in templates:
            continue
        dates = DATE_RE.findall(row["target"])
        if len(dates) != 2:
            continue
        templates.add(record["template_id"])
        original = {**row, "probe": "dev-iso", "template_id": record["template_id"]}
        probes.append(original)
        natural = copy.deepcopy(original)
        natural["probe"] = "dev-natural-date"
        # Hold intent and target fixed; change only rendering of the same date interval.
        start, end = [date.fromisoformat(d) for d in dates]
        days = (end - start).days
        date_text = f"the {days} days beginning {start.strftime('%B')} {start.day}, {start.year}"
        content = natural["messages"][1]["content"]
        content = re.sub(
            r"Window: from \d{4}-\d\d-\d\d up to but excluding \d{4}-\d\d-\d\d\.",
            f"Window: {date_text}.",
            content,
        )
        if content == natural["messages"][1]["content"]:
            raise ValueError("Expected a formal ISO date interval")
        natural["messages"][1]["content"] = content
        probes.append(natural)
        if len(templates) == 8:
            break
    if len(probes) != 16:
        raise ValueError("Expected eight paired development probes")
    cfg.write_jsonl(WORK / "dev-probes.jsonl", probes)
    original_manifest = original_output_manifest()
    spec = {
        "attempt": attempt,
        "evaluation_role": "development",
        "variants": VARIANTS,
        "candidate": "dates-columns",
        "smoke_prefix": 10,
        "full_rows": 100,
        "scope": "inference prompt intervention on frozen T11B adapter, no retraining",
        "stop_if_smoke_fails": True,
        "matched_base_control": "b3-base/dates-columns",
        "original_archive_sha256": cfg.sha256_file(REPORT / "b3-seed-42/artifacts.zip"),
        "adapter_sha256": tree_digest(ORIGINAL / "adapter"),
        "original_output_files": original_manifest,
        "generator": cfg.load()["models"]["generator"],
        "generation": cfg.load()["generation"],
        "original_predictions_sha256": cfg.sha256_file(ORIGINAL / "predictions-dev_eval.jsonl"),
        "input_sha256": {
            p: cfg.sha256_file(WORK / p) for p in ("prompts.jsonl", "dev-probes.jsonl")
        },
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    }
    files = sorted((ROOT / "src").rglob("*.py"))
    files += [
        ROOT / "scripts/t11b_diagnose.py",
        ROOT / "scripts/t11a.py",
        ROOT / "configs/experiment.toml",
        ROOT / "configs/t11b-gpu-requirements.txt",
        ROOT / "configs/t11-model-files.json",
        WORK / "prompts.jsonl",
        WORK / "dev-probes.jsonl",
    ]
    spec["files"] = {p.relative_to(ROOT).as_posix(): cfg.sha256_file(p) for p in files}
    plan_dir = WORK if attempt == 1 else WORK / f"attempts/v{attempt}"
    cfg.write_json(plan_dir / "plan.json", spec)
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(ROOT))
        z.write(plan_dir / "plan.json", (WORK / "plan.json").relative_to(ROOT))
    cfg.write_json(
        plan_dir / "bundle.json",
        {"sha256": cfg.sha256_file(archive), "bytes": archive.stat().st_size},
    )
    print(json.dumps({"archive": str(archive), "prompts": len(prompts), "dev_probes": len(probes)}))


def gpu(home: Path) -> None:
    print("Starting: import-torch", flush=True)
    import torch
    from t11a import verify_cache

    from eth_nl2sql.generation.backend import load_generator
    from eth_nl2sql.train_qlora import PaddingCollator, encode_row

    os.environ.update(
        HF_HOME=str(home),
        HF_HUB_CACHE=str(home / "hub"),
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    spec = json.loads((WORK / "plan.json").read_text())
    for path, expected in spec["files"].items():
        if cfg.sha256_file(ROOT / path) != expected:
            raise ValueError(f"Input mismatch: {path}")
    adapter = WORK / "frozen-adapter"
    outputs = WORK / "output"
    outputs.mkdir(exist_ok=False)
    status = {"status": "running", "full_evaluation_allowed": False}
    monitor = None
    started = time.monotonic()
    try:
        print("Starting: verify-direct-adapter-files", flush=True)
        source = Path(
            "/kaggle/input/notebooks/aohkvd/eth-nl2sql-t11b-b3-seed-42-20261028/eth-nl2sql"
        )
        for name, expected in spec["original_output_files"].items():
            prefix = "runs/b3/seed-42/adapter/"
            if name.startswith(prefix):
                data = (source / name).read_bytes()
                if hashlib.sha256(data).hexdigest() != expected:
                    raise ValueError(f"Adapter mismatch: {name}")
                destination = adapter / name.removeprefix(prefix)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(data)
        if tree_digest(adapter) != spec["adapter_sha256"]:
            raise ValueError("Frozen adapter digest mismatch")
        print("Completed: verify-direct-adapter-files", flush=True)
        print("Starting: verify-model-cache", flush=True)
        cache = verify_cache(home, ROOT / "configs/t11-model-files.json")
        cfg.write_json(outputs / "model-cache-verification.json", cache)
        print("Completed: verify-model-cache", flush=True)
        print("Starting: resource-monitor", flush=True)
        monitor = ResourceMonitor()
        print("Completed: resource-monitor", flush=True)
        settings = cfg.load()
        backend = HuggingFaceGenerationBackend()
        backend.seed(42)
        print("Starting: load-tokenizer", flush=True)
        tokenizer = backend.tokenizer(settings)
        print("Completed: load-tokenizer", flush=True)
        print("Starting: load-model", flush=True)
        model, _ = load_generator(settings, adapter=adapter, tokenizer=tokenizer)
        print("Completed: load-model", flush=True)
        tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
        probes = cfg.read_jsonl(WORK / "dev-probes.jsonl")
        encoded = [encode_row(tokenizer, p, 8192) for p in probes[:2]]
        batch = {
            k: v.to(model.device)
            for k, v in PaddingCollator(tokenizer.pad_token_id)(encoded).items()
        }
        with torch.inference_mode():
            out = model(**batch)
            labels = batch["labels"][:, 1:]
            manual = torch.nn.functional.cross_entropy(
                out.logits[:, :-1].float().reshape(-1, out.logits.shape[-1]),
                labels.reshape(-1),
                ignore_index=-100,
            )
        loss_audit = {
            "model_loss": out.loss.item(),
            "manual_shifted_sql_eot_loss": manual.item(),
            "absolute_difference": abs(out.loss.item() - manual.item()),
            "unmasked_sql_eot_tokens": int((labels != -100).sum()),
            "padding_labels_all_masked": bool(
                (batch["labels"][batch["attention_mask"] == 0] == -100).all()
            ),
            "targets_complete": all(
                [t for t in e["labels"] if t != -100]
                == tokenizer(p["target"], add_special_tokens=False)["input_ids"]
                + [stop_token_ids(tokenizer)[-1]]
                for e, p in zip(encoded, probes[:2], strict=True)
            ),
            "torch": torch.__version__,
            "transformers": __import__("transformers").__version__,
        }
        cfg.write_json(outputs / "loss-audit.json", loss_audit)
        del out, batch, manual
        if (
            loss_audit["absolute_difference"] > 1e-4
            or not loss_audit["targets_complete"]
            or not loss_audit["padding_labels_all_masked"]
        ):
            raise ValueError("Loss/masking audit failed")

        probe_losses = []
        for probe in probes:
            feature = encode_row(tokenizer, probe, 8192)
            inputs = {
                k: v.to(model.device)
                for k, v in PaddingCollator(tokenizer.pad_token_id)([feature]).items()
            }
            with torch.inference_mode():
                loss = model(**inputs).loss.item()
            probe_losses.append(
                {"id": probe["id"], "probe": probe["probe"], "teacher_forced_loss": loss}
            )
        cfg.write_jsonl(outputs / "probe-losses.jsonl", probe_losses)

        def generate(rows, path):
            done = cfg.read_jsonl(path) if path.exists() else []
            if len(done) > len(rows):
                raise ValueError("Cannot replace a longer generation")
            for row in rows[len(done) :]:
                if (
                    len(tokenizer.apply_chat_template(row["messages"], add_generation_prompt=True))
                    + settings["generation"]["max_new_tokens"]
                    > 8192
                ):
                    raise ValueError("Prompt exceeds context")
                prediction = backend.generate(model, tokenizer, row, settings)
                prediction.update(id=row["id"], prompt_sha256=messages_digest(row["messages"]))
                with path.open("a") as f:
                    f.write(json.dumps(prediction) + "\n")
                done.append(prediction)
                print(path.name, len(done), row["id"], flush=True)
            return done

        for probe in ("dev-iso", "dev-natural-date"):
            generate([r for r in probes if r["probe"] == probe], outputs / f"{probe}.jsonl")
        prompts = cfg.read_jsonl(WORK / "prompts.jsonl")
        by_variant = {v: [r for r in prompts if r["variant"] == v] for v in VARIANTS}
        for variant, rows in by_variant.items():
            predictions = generate(rows[:10], outputs / f"b3-{variant}.jsonl")
            cfg.write_json(outputs / f"smoke-b3-{variant}.json", inspect_predictions(predictions))
        gate = json.loads((outputs / "smoke-b3-dates-columns.json").read_text())
        status["full_evaluation_allowed"] = gate["passed"]
        # Both arms use byte-identical messages. Only adapter activation changes.
        with model.disable_adapter():
            base = generate(
                by_variant["dates-columns"][:10], outputs / "b3-base-dates-columns.jsonl"
            )
            cfg.write_json(outputs / "smoke-b3-base-dates-columns.json", inspect_predictions(base))
        if gate["passed"]:
            generate(by_variant["dates-columns"], outputs / "b3-dates-columns.jsonl")
            with model.disable_adapter():
                generate(by_variant["dates-columns"], outputs / "b3-base-dates-columns.jsonl")
        status["status"] = "complete" if gate["passed"] else "stopped_at_smoke"
    except BaseException as exc:
        status.update(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        cfg.write_json(outputs / "status.json", status)
        cfg.write_json(
            outputs / "resources.json",
            monitor.summary() if monitor else {"startup_failed": True},
        )
        cfg.write_json(outputs / "wall-runtime.json", {"runtime_s": time.monotonic() - started})
        cfg.write_json(outputs / "plan.json", spec)
        files = [p for p in sorted(outputs.rglob("*")) if p.is_file()]
        cfg.write_json(outputs / "manifest.json", {p.name: cfg.sha256_file(p) for p in files})
        with zipfile.ZipFile(
            ROOT.parent / "t11b-diagnosis-artifacts.zip", "w", zipfile.ZIP_DEFLATED
        ) as z:
            for p in [*files, outputs / "manifest.json"]:
                z.write(p, p.name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("audit", "prepare", "gpu"))
    parser.add_argument("--archive", type=Path, default=ROOT / ".cache/t11b-diagnosis-inputs.zip")
    parser.add_argument("--hf-home", type=Path)
    parser.add_argument("--attempt", type=int, default=1)
    args = parser.parse_args()
    if args.stage == "audit":
        audit()
    elif args.stage == "prepare":
        prepare(args.archive, attempt=args.attempt)
    else:
        gpu(args.hf_home)
