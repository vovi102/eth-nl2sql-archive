"""Verify and evaluate frozen-adapter diagnostic artifacts without SQL edits."""

from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from t11b_diagnose import DATE_RE, ORIGINAL, ROOT, VARIANTS, WORK, original_output_manifest

from eth_nl2sql import config as cfg
from eth_nl2sql.evaluate import case_rows, evaluate_predictions, summarize
from eth_nl2sql.experiments import tree_digest
from eth_nl2sql.generation.prompt import messages_digest
from eth_nl2sql.gpu_workflow import collect_outputs
from eth_nl2sql.store.build import connect
from eth_nl2sql.store.manifest import store_profile


def collect(archive: Path) -> None:
    manifest = collect_outputs(
        WORK / "output",
        archive,
        "manifest.json",
        can_replace=lambda _: False,
        expected_json={"plan.json": json.loads((WORK / "plan.json").read_text())},
    )
    cfg.write_json(
        WORK / "download.json",
        {
            "sha256": cfg.sha256_file(archive),
            "bytes": archive.stat().st_size,
            "verified_files": len(manifest),
        },
    )


def checked_predictions(
    path: Path, prompts: list[dict], *, sizes: tuple[int, ...] = (10, 100)
) -> list[dict]:
    rows = cfg.read_jsonl(path)
    if len(rows) not in sizes or [r["id"] for r in rows] != [r["id"] for r in prompts[: len(rows)]]:
        raise ValueError(f"Incomplete, reordered, or duplicate predictions: {path}")
    for row, prompt in zip(rows, prompts, strict=False):
        if row["prompt_sha256"] != messages_digest(prompt["messages"]):
            raise ValueError(f"Prompt hash mismatch for {row['id']}")
    return rows


def evaluate() -> dict:
    outputs = WORK / "output"
    raw_manifest = json.loads((outputs / "manifest.json").read_text())
    for name, expected in raw_manifest.items():
        if cfg.sha256_file(outputs / name) != expected:
            raise ValueError(f"Diagnostic output changed: {name}")
    for name, expected in original_output_manifest().items():
        if cfg.sha256_file(ROOT / name) != expected:
            raise ValueError(f"Original T11B artifact changed: {name}")
    if (
        tree_digest(ORIGINAL / "adapter")
        != json.loads((WORK / "evidence.json").read_text())["adapter_sha256"]
    ):
        raise ValueError("Original adapter changed")
    settings = cfg.load()["evaluation"]
    dev_eval = {r["id"]: r for r in cfg.read_jsonl(ROOT / "data/dev_eval.jsonl")}
    prompts = cfg.read_jsonl(WORK / "prompts.jsonl")
    summary, prefixes, paired = {}, {}, {}
    evaluated = WORK / "evaluation"
    evaluated.mkdir(exist_ok=True)
    with connect(cfg.STORE_PATH) as con:
        profile = store_profile(con)

        def score(name, predictions, cases):
            results = evaluate_predictions(
                con,
                cases,
                {r["id"]: r for r in predictions},
                float_digits=settings["float_digits"],
                timeout_s=settings["timeout_s"],
            )
            result = summarize(
                results, samples=settings["bootstrap_samples"], seed=settings["bootstrap_seed"]
            )
            result.update(
                evaluation_role="development",
                store=profile,
                scope=f"{len(cases)} development cases; frozen-adapter inference intervention",
            )
            result["date_literals_match_gold"] = sum(
                DATE_RE.findall(p["raw_output"]) == DATE_RE.findall(c["sql"])
                for p, c in zip(predictions, cases, strict=True)
            )
            cfg.write_json(evaluated / f"{name}.json", result)
            cfg.write_jsonl(evaluated / f"{name}-cases.jsonl", case_rows(results))
            return result

        for variant in (*VARIANTS, "base-dates-columns"):
            path = outputs / f"b3-{variant}.jsonl"
            if not path.exists():
                continue
            arm = "dates-columns" if variant.startswith("base-") else variant
            arm_prompts = [r for r in prompts if r["variant"] == arm]
            predictions = checked_predictions(path, arm_prompts)
            cases = [dev_eval[r["id"]] for r in predictions]
            summary[variant] = score(variant, predictions, cases)
            prefixes[variant] = score(f"{variant}-prefix10", predictions[:10], cases[:10])
        probes = cfg.read_jsonl(WORK / "dev-probes.jsonl")
        for name in ("dev-iso", "dev-natural-date"):
            expected = [r for r in probes if r["probe"] == name]
            predictions = checked_predictions(outputs / f"{name}.jsonl", expected, sizes=(8,))
            cases = [dict(id=r["id"], sql=r["target"]) for r in expected]
            paired[name] = score(name, predictions, cases)
    original_rows = cfg.read_jsonl(ORIGINAL / "predictions-dev_eval.jsonl")
    replay = cfg.read_jsonl(outputs / "b3-original.jsonl")
    replay_equal = all(
        a["id"] == b["id"] and a["raw_output"] == b["raw_output"]
        for a, b in zip(original_rows, replay, strict=True)
    )
    losses = defaultdict(list)
    for r in cfg.read_jsonl(outputs / "probe-losses.jsonl"):
        losses[r["probe"]].append(r["teacher_forced_loss"])
    candidate = summary.get("dates-columns", {})
    gate = json.loads((outputs / "smoke-b3-dates-columns.json").read_text())
    loss_audit = json.loads((outputs / "loss-audit.json").read_text())
    resources = json.loads((outputs / "resources.json").read_text())
    issues = []
    if not replay_equal:
        issues.append("Original prompt no longer reproduces the original SQL byte for byte")
    if any(not math.isfinite(v) for values in losses.values() for v in values):
        issues.append("Non-finite paired development loss")
    if not math.isfinite(loss_audit["model_loss"]) or loss_audit["absolute_difference"] > 1e-4:
        issues.append("Manual shifted loss does not verify model loss")
    if not resources["hardware"]["gpus"] or not resources["peak_gpu_memory_gib"]:
        issues.append("Missing actual GPU resource measurements")
    if not gate["passed"] and candidate.get("n", 0) > 10:
        raise ValueError("Full generation bypassed a failed smoke gate")
    ready = (
        gate["passed"]
        and candidate.get("n") == 100
        and candidate["valid_sql_rate"] > 0
        and candidate["execution_accuracy"] > 0
        and summary.get("base-dates-columns", {}).get("n") == 100
        and not issues
    )
    result = {
        "decision": "ready_for_review_before_scaling" if ready else "stop_for_further_diagnosis",
        "original_replay_sql_identical": replay_equal,
        "prefix10": prefixes,
        "all_generated": summary,
        "paired_dev": paired,
        "mean_teacher_forced_loss": {k: sum(v) / len(v) for k, v in losses.items()},
        "loss_audit": loss_audit,
        "resources": resources,
        "issues": issues,
        "smoke_passed": gate["passed"],
        "full_rows": candidate.get("n", 0),
        "new_training": False,
        "expanded_seeds": False,
    }
    cfg.write_json(WORK / "review.json", result)
    cfg.write_json(
        evaluated / "manifest.json",
        {
            path.name: cfg.sha256_file(path)
            for path in sorted(evaluated.iterdir())
            if path.is_file() and path.name != "manifest.json"
        },
    )
    write_report(result)
    print(
        json.dumps(
            {
                "decision": result["decision"],
                "smoke_passed": gate["passed"],
                "full_rows": result["full_rows"],
                "prefix10": {
                    k: {
                        m: v[m]
                        for m in (
                            "n",
                            "valid_sql_rate",
                            "execution_accuracy",
                            "date_literals_match_gold",
                        )
                    }
                    for k, v in prefixes.items()
                },
                "paired_loss": result["mean_teacher_forced_loss"],
            }
        )
    )
    return result


def write_report(result: dict) -> None:
    lines = [
        "# T11B — chẩn đoán trên adapter đóng băng",
        "",
        "## Material Passport",
        "",
        "- Origin Skill: academic-research-suite / experiment-agent",
        "- Origin Mode: run",
        "- Origin Date: 2026-10-29 (Asia/Saigon)",
        f"- Verification Status: {'VERIFIED' if not result['issues'] else 'ANALYZED'} "
        "(hash và chấm local; không phải kết quả test)",
        "- Version Label: t11b_diagnosis_v1",
        "",
        "Giữ nguyên adapter và dự đoán T11B. Các can thiệp chỉ đổi prompt lúc suy luận; "
        "không có lượt QLoRA mới. Mỗi nhánh dùng cùng 10 câu đầu dev_eval, seed greedy 42, "
        "model/revision và runtime đã khóa. Thiết kế 2×2 được ghi trước khi submit.",
        "",
        "| Prompt, cùng 10 câu | Compile | EX | Literal ngày khớp gold |",
        "|---|---:|---:|---:|",
    ]
    for name, row in result["prefix10"].items():
        lines.append(
            f"| {name} | {round(row['valid_sql_rate'] * row['n'])}/{row['n']} | "
            f"{round(row['execution_accuracy'] * row['n'])}/{row['n']} | "
            f"{row['date_literals_match_gold']}/{row['n']} |"
        )
    lines += [
        "",
        "| Cặp dev (8 ý định, chỉ đổi cách viết ngày) | EX | Loss teacher forcing trung bình |",
        "|---|---:|---:|",
    ]
    for name, row in result["paired_dev"].items():
        lines.append(
            f"| {name} | {round(row['execution_accuracy'] * row['n'])}/{row['n']} | "
            f"{result['mean_teacher_forced_loss'][name]:.8g} |"
        )
    audit = result["loss_audit"]
    lines += [
        "",
        f"Model loss = {audit['model_loss']:.9g}; cross-entropy dịch một token, "
        f"chỉ SQL+EOT = {audit['manual_shifted_sql_eot_loss']:.9g}; "
        f"sai khác tuyệt đối {audit['absolute_difference']:.3g}. "
        f"Target đầy đủ: {audit['targets_complete']}; padding được mask: "
        f"{audit['padding_labels_all_masked']}. "
        f"Runtime thực tế: Transformers {audit['transformers']}, torch {audit['torch']}.",
        "",
        f"Replay prompt gốc sinh SQL giống từng byte: {result['original_replay_sql_identical']}.",
        "",
    ]
    if result["full_rows"] == 100:
        lines += [
            "Nhánh kết hợp qua smoke 10/10 trước khi sinh tiếp. Kết quả đủ 100 câu:",
            "",
            "| Nhánh | Compile | EX |",
            "|---|---:|---:|",
        ]
        for name in ("dates-columns", "base-dates-columns"):
            row = result["all_generated"][name]
            lines.append(
                f"| {name} | {round(row['valid_sql_rate'] * 100)}/100 | "
                f"{round(row['execution_accuracy'] * 100)}/100 |"
            )
    else:
        lines += [
            f"Smoke nhánh kết hợp passed={result['smoke_passed']}; chỉ có "
            f"{result['full_rows']} câu. Chưa đánh giá đủ 100 câu và chưa được mở rộng seed."
        ]
    resources = result["resources"]
    lines += [
        "",
        f"Quyết định: **{result['decision']}**. Chưa chạy b3l/42 hoặc các seed còn lại.",
        "",
        "Mọi EX ở đây dùng DuckDB sample phát triển. Mười câu đầu và tám cặp dev "
        "là phép chẩn đoán nhỏ, không chứng minh tổng quát hóa cho test. Test v2 không "
        "được dùng. Khác biệt literal ngày chỉ là số đo chẩn đoán, không thay EX.",
        "",
        f"Tài nguyên chung cho toàn bộ job sau khi chuẩn bị adapter: "
        f"{resources['runtime_s']:.3f} giây; GPU {resources['hardware']['gpus']}; "
        f"peak allocated từng GPU {resources['per_gpu_peak_allocated_gib']} GiB. "
        "Không phân bổ số đo chung này thành runtime riêng cho từng nhánh.",
        "",
        "Xem [review có số đo đầy đủ](review.json), [kế hoạch trước khi chạy](plan.json), "
        "[checksum output](output/manifest.json), [bằng chứng gốc](evidence.json).",
    ]
    if result["issues"]:
        lines += ["", "Vấn đề cần giải quyết:", "", *[f"- {issue}" for issue in result["issues"]]]
    (WORK / "README.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("collect", "evaluate"))
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    if args.stage == "collect":
        collect(args.archive)
    else:
        evaluate()
