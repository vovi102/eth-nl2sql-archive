"""Command line entry point: `eth-nl2sql <command>`.

Typical order:
  snapshot-plan / snapshot-run   one-time BigQuery extraction (needs the `bq` extra)
  build-store, parity            local DuckDB replica and its fidelity check
  link, prompts                  linking hints and rendered prompts (needs `embed`)
  generate, train                on a Kaggle T4 (needs `gpu`)
  evaluate, report               execution accuracy and the results table
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from eth_nl2sql import config as cfg

RUNS_DIR = cfg.ROOT / "runs"
SPLITS = {
    "train": cfg.DATA_DIR / "train.jsonl",
    "dev": cfg.DATA_DIR / "dev.jsonl",
    "test": cfg.DATA_DIR / "test.jsonl",
}


def _git_commit() -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(cfg.ROOT), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _print(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False, default=str))


def cmd_snapshot_plan(args: argparse.Namespace) -> None:
    from eth_nl2sql.store import snapshot

    _print(snapshot.plan(args.project))


def cmd_snapshot_run(args: argparse.Namespace) -> None:
    from eth_nl2sql.store import snapshot

    _print(snapshot.run(args.project, args.parquet))


def cmd_build_store(args: argparse.Namespace) -> None:
    from eth_nl2sql.store.build import build_store

    _print(build_store(args.store, args.parquet, args.labels / "entities.json"))


def cmd_parity(args: argparse.Namespace) -> None:
    from eth_nl2sql.store.build import connect
    from eth_nl2sql.store.parity import check

    fixtures = cfg.ROOT / "tests" / "fixtures"
    report = check(
        connect(args.store), fixtures / "bq_gold_results.json", fixtures / "stage_a_witnesses.json"
    )
    cfg.write_json(RUNS_DIR / "parity.json", report)
    _print({key: report[key] for key in ("gold_exact", "witness_row_counts", "passed")})


def cmd_check_sql(args: argparse.Namespace) -> None:
    """Compile every gold and training query against an empty store (no data needed)."""
    from eth_nl2sql.store.build import connect, create_schema
    from eth_nl2sql.store.execute import ExecutionError, execute
    from eth_nl2sql.validation import ValidationError

    con = connect()
    create_schema(con)
    failures = []
    total = 0
    for split, path in SPLITS.items():
        for sql in sorted({row["sql"] for row in cfg.read_jsonl(path)}):
            total += 1
            try:
                execute(con, sql)
            except (ValidationError, ExecutionError) as exc:
                failures.append({"split": split, "code": exc.code, "error": str(exc), "sql": sql})
    _print({"checked": total, "failures": failures})
    if failures:
        sys.exit(1)


def cmd_check_data(args: argparse.Namespace) -> None:
    from eth_nl2sql.data.audit import audit_import, render_report

    protected = {p.resolve() for p in args.directory.glob("*") if p.is_file()}
    if args.out.resolve() in protected or args.report.resolve() in protected:
        raise SystemExit("Report paths must not overwrite files in the input directory")
    if args.out.resolve() == args.report.resolve():
        raise SystemExit("JSON and Markdown report paths must be different")
    report = audit_import(args.directory, progress=lambda message: print(message, file=sys.stderr))
    cfg.write_json(args.out, report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_report(report))
    _print(
        {
            "passed": report["passed"],
            "integrity_ok": report["integrity_ok"],
            "quality_ok": report["quality_ok"],
            "store_schema_complete": report["store_schema_complete"],
            "out": str(args.out),
            "report": str(args.report),
        }
    )
    if not report["passed"]:
        sys.exit(1)


def _linking_pipeline(dictionary_dir: Path, *, use_encoder: bool):
    from eth_nl2sql.linking.context import LinkingPipeline
    from eth_nl2sql.linking.dictionary import load_dictionary
    from eth_nl2sql.linking.entity import EntityLinker
    from eth_nl2sql.linking.schema import SchemaLinker

    encoder = None
    if use_encoder:
        from eth_nl2sql.generation.retrieval import load_encoder

        encoder = load_encoder(cfg.load())
    dictionary = load_dictionary(dictionary_dir)
    catalog = json.loads(cfg.CATALOG_PATH.read_text())
    synonyms = json.loads(cfg.SYNONYMS_PATH.read_text())
    return LinkingPipeline(
        dictionary, SchemaLinker(catalog, synonyms, encoder), EntityLinker(dictionary, encoder)
    )


def cmd_link(args: argparse.Namespace) -> None:
    pipeline = _linking_pipeline(args.dictionary, use_encoder=not args.no_encoder)
    rows = [
        {
            "id": row["id"],
            "question": row["question"],
            "linking": pipeline.link(row["question"]).to_json(),
        }
        for row in cfg.read_jsonl(SPLITS[args.split])
    ]
    out = cfg.DATA_DIR / "linking" / f"{args.split}.jsonl"
    cfg.write_jsonl(out, rows)
    _print({"split": args.split, "rows": len(rows), "out": str(out)})


def _load_linkings(split: str) -> dict:
    from eth_nl2sql.linking.context import Linking

    path = cfg.DATA_DIR / "linking" / f"{split}.jsonl"
    if not path.exists():
        raise SystemExit(f"missing {path}; run `eth-nl2sql link --split {split}` first")
    return {row["id"]: Linking.from_json(row["linking"]) for row in cfg.read_jsonl(path)}


def cmd_prompts(args: argparse.Namespace) -> None:
    from eth_nl2sql.generation.runs import CONFIGS, prompt_rows, training_rows

    run = CONFIGS[args.config]
    catalog = json.loads(cfg.CATALOG_PATH.read_text())
    out_dir = RUNS_DIR / run.name
    if args.training:
        for split in ("train", "dev"):
            linkings = _load_linkings(split) if run.linking else None
            rows = training_rows(
                run, cfg.read_jsonl(SPLITS[split]), catalog=catalog, linkings=linkings
            )
            cfg.write_jsonl(out_dir / f"sft-{split}.jsonl", rows)
        _print({"config": run.name, "out": str(out_dir)})
        return
    retrieve = None
    if run.examples:
        from eth_nl2sql.generation.retrieval import FewShotRetriever, load_encoder

        experiment = cfg.load()
        retriever = FewShotRetriever(
            cfg.read_jsonl(SPLITS["train"]),
            load_encoder(experiment),
            k=experiment["retrieval"]["examples"],
        )

        def retrieve(case):
            return retriever.retrieve(case["question"], exclude_family=case.get("family_id"))

    rows = prompt_rows(
        run,
        cfg.read_jsonl(SPLITS[args.split]),
        catalog=catalog,
        linkings=_load_linkings(args.split) if run.linking else None,
        retrieve=retrieve,
    )
    out = out_dir / f"prompts-{args.split}.jsonl"
    cfg.write_jsonl(out, rows)
    _print({"config": run.name, "split": args.split, "rows": len(rows), "out": str(out)})


def _run_record(run_name: str, extra: dict) -> None:
    record = {
        "config": run_name,
        "git_commit": _git_commit(),
        "experiment_sha256": cfg.sha256_file(cfg.CONFIG_PATH),
        "catalog_sha256": cfg.sha256_file(cfg.CATALOG_PATH),
        **extra,
    }
    cfg.write_json(RUNS_DIR / run_name / "run.json", record)


def cmd_generate(args: argparse.Namespace) -> None:
    from eth_nl2sql.generation.backend import generate_file

    out_dir = RUNS_DIR / args.config
    prompts = out_dir / f"prompts-{args.split}.jsonl"
    written = generate_file(
        prompts,
        out_dir / f"predictions-{args.split}.jsonl",
        cfg.load(),
        adapter=args.adapter,
        limit=args.limit,
    )
    _run_record(
        args.config,
        {
            "split": args.split,
            "prompts_sha256": cfg.sha256_file(prompts),
            "adapter": str(args.adapter) if args.adapter else None,
        },
    )
    _print({"config": args.config, "generated": written})


def cmd_train(args: argparse.Namespace) -> None:
    from eth_nl2sql.train_qlora import train

    out_dir = RUNS_DIR / args.config
    summary = train(out_dir / "sft-train.jsonl", out_dir / "sft-dev.jsonl", out_dir, cfg.load())
    _print({k: v for k, v in summary.items() if k != "log_history"})


def cmd_echo_gold(args: argparse.Namespace) -> None:
    rows = [
        {"id": row["id"], "config": "gold-echo", "raw_output": row["sql"], "latency_ms": None}
        for row in cfg.read_jsonl(SPLITS[args.split])
    ]
    cfg.write_jsonl(RUNS_DIR / "gold-echo" / f"predictions-{args.split}.jsonl", rows)
    _print({"rows": len(rows)})


def cmd_evaluate(args: argparse.Namespace) -> None:
    from eth_nl2sql.evaluate import case_rows, evaluate_predictions, summarize
    from eth_nl2sql.store.build import connect

    settings = cfg.load()["evaluation"]
    out_dir = RUNS_DIR / args.config
    predictions_path = out_dir / f"predictions-{args.split}.jsonl"
    predictions = {row["id"]: row for row in cfg.read_jsonl(predictions_path)}
    cases = cfg.read_jsonl(SPLITS[args.split])
    results = evaluate_predictions(
        connect(args.store),
        cases,
        predictions,
        float_digits=settings["float_digits"],
        timeout_s=settings["timeout_s"],
    )
    summary = summarize(
        results, samples=settings["bootstrap_samples"], seed=settings["bootstrap_seed"]
    )
    summary.update(
        {
            "config": args.config,
            "split": args.split,
            "missing_predictions": sorted({c["id"] for c in cases} - set(predictions)),
            "predictions_sha256": cfg.sha256_file(predictions_path),
            "test_sha256": cfg.sha256_file(SPLITS[args.split]),
        }
    )
    cfg.write_jsonl(out_dir / f"cases-{args.split}.jsonl", case_rows(results))
    cfg.write_json(out_dir / f"eval-{args.split}.json", summary)
    _print(
        {k: summary[k] for k in ("execution_accuracy", "execution_accuracy_ci95", "valid_sql_rate")}
    )


def cmd_report(args: argparse.Namespace) -> None:
    from eth_nl2sql.report import write_report

    path = write_report(RUNS_DIR, args.split, cfg.ROOT / "RESULTS.md")
    _print({"written": str(path)})


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="eth-nl2sql", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    def add(name: str, handler, help_text: str) -> argparse.ArgumentParser:
        command = sub.add_parser(name, help=help_text)
        command.set_defaults(handler=handler)
        return command

    for name, handler, text in (
        ("snapshot-plan", cmd_snapshot_plan, "dry-run the BigQuery extraction (free)"),
        ("snapshot-run", cmd_snapshot_run, "run the BigQuery extraction (uses quota)"),
    ):
        command = add(name, handler, text)
        command.add_argument("--project", required=True)
        command.add_argument("--parquet", type=Path, default=cfg.PARQUET_DIR)

    command = add("build-store", cmd_build_store, "build the DuckDB store from parquet")
    command.add_argument("--parquet", type=Path, default=cfg.PARQUET_DIR)
    command.add_argument("--labels", type=Path, default=cfg.DATA_DIR / "entities" / "v1")
    command.add_argument("--store", type=Path, default=cfg.STORE_PATH)

    command = add("parity", cmd_parity, "compare local results with BigQuery observations")
    command.add_argument("--store", type=Path, default=cfg.STORE_PATH)

    add("check-sql", cmd_check_sql, "compile all dataset SQL against an empty store")

    command = add("check-data", cmd_check_data, "verify and profile the imported LuanVan CSV data")
    command.add_argument("--directory", type=Path, default=cfg.DATA_DIR / "raw" / "luanvan")
    command.add_argument(
        "--out", type=Path, default=cfg.ROOT / "reports" / "data-quality" / "luanvan.json"
    )
    command.add_argument(
        "--report", type=Path, default=cfg.ROOT / "reports" / "data-quality" / "luanvan.md"
    )

    command = add("link", cmd_link, "compute linking hints for a split")
    command.add_argument("--split", choices=SPLITS, required=True)
    command.add_argument("--dictionary", type=Path, default=cfg.DATA_DIR / "entities" / "v1")
    command.add_argument("--no-encoder", action="store_true", help="lexical/fuzzy stages only")

    command = add("prompts", cmd_prompts, "render prompts (or SFT rows) for a configuration")
    command.add_argument("--config", required=True)
    command.add_argument("--split", choices=SPLITS, default="test")
    command.add_argument("--training", action="store_true", help="write SFT train/dev rows")

    command = add("generate", cmd_generate, "generate SQL for rendered prompts (GPU)")
    command.add_argument("--config", required=True)
    command.add_argument("--split", choices=SPLITS, default="test")
    command.add_argument("--adapter", type=Path)
    command.add_argument("--limit", type=int)

    command = add("train", cmd_train, "QLoRA fine-tuning for b3/b3l (GPU)")
    command.add_argument("--config", choices=("b3", "b3l"), required=True)

    command = add("echo-gold", cmd_echo_gold, "write gold SQL as predictions (pipeline check)")
    command.add_argument("--split", choices=SPLITS, default="test")

    command = add("evaluate", cmd_evaluate, "score predictions on the local store")
    command.add_argument("--config", required=True)
    command.add_argument("--split", choices=SPLITS, default="test")
    command.add_argument("--store", type=Path, default=cfg.STORE_PATH)

    command = add("report", cmd_report, "write RESULTS.md from evaluated runs")
    command.add_argument("--split", choices=SPLITS, default="test")

    args = parser.parse_args(argv)
    args.handler(args)


if __name__ == "__main__":
    main()
