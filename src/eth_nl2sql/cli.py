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
from eth_nl2sql.data.splits import read_split, split_paths

RUNS_DIR = cfg.ROOT / "runs"
SPLITS = split_paths()


def _read_split(name: str, dictionary: Path = cfg.DICTIONARY_DIR) -> list[dict]:
    try:
        if name == "test":
            from eth_nl2sql.data.benchmark import require_frozen

            require_frozen(SPLITS["test"].parent, cfg.DATA_DIR, dictionary)
        return read_split(name)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


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

    report = snapshot.plan(args.project, location=args.location, budget_bytes=args.budget_bytes)
    cfg.write_json(args.out, report)
    _print({k: v for k, v in report.items() if k != "partitions"})
    if not report["passed"]:
        raise SystemExit(1)


def cmd_snapshot_run(args: argparse.Namespace) -> None:
    from eth_nl2sql.store import snapshot

    try:
        report = snapshot.run(
            args.project,
            args.parquet,
            location=args.location,
            budget_bytes=args.budget_bytes,
            storage_api=args.storage_api,
        )
    except Exception as exc:
        report = {
            "passed": False,
            "status": "stopped",
            "project": args.project,
            "parquet": str(args.parquet),
            "error": f"{type(exc).__name__}: {exc}",
        }
        cfg.write_json(args.out, report)
        _print(report)
        raise SystemExit(1) from exc
    cfg.write_json(args.out, report)
    _print(report)


def cmd_snapshot_validate(args: argparse.Namespace) -> None:
    from eth_nl2sql.store.quality import validate_snapshot

    report = validate_snapshot(args.parquet)
    cfg.write_json(args.out, report)
    _print(report)
    if not report["passed"]:
        raise SystemExit(1)


def cmd_build_store(args: argparse.Namespace) -> None:
    from eth_nl2sql.linking.dictionary import load_dictionary
    from eth_nl2sql.store.build import build_store

    load_dictionary(args.labels)
    _print(build_store(args.store, args.parquet, args.labels / "entities.json"))


def cmd_check_dictionary(args: argparse.Namespace) -> None:
    from eth_nl2sql.linking.audit import check_dictionary

    _print(check_dictionary(args.dictionary))


def cmd_dictionary_coverage(args: argparse.Namespace) -> None:
    from eth_nl2sql.linking.audit import coverage_gate, dictionary_coverage, render_coverage
    from eth_nl2sql.store.build import connect

    protected = {
        args.store.resolve(),
        *(p.resolve() for p in args.dictionary.rglob("*") if p.is_file()),
    }
    if args.baseline:
        protected.add(args.baseline.resolve())
    if args.out.resolve() in protected or args.report.resolve() in protected:
        raise SystemExit("Coverage output must not overwrite the dictionary or store")
    if args.out.resolve() == args.report.resolve():
        raise SystemExit("JSON and Markdown report paths must be different")
    with connect(args.store) as con:
        report = dictionary_coverage(con, args.dictionary)
    if args.baseline:
        report["coverage_gate"] = coverage_gate(report, json.loads(args.baseline.read_text()))
        report["coverage_gate"]["baseline_sha256"] = cfg.sha256_file(args.baseline)
    cfg.write_json(args.out, report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_coverage(report))
    summary = {**report["summary"], "out": str(args.out), "report": str(args.report)}
    if args.baseline:
        summary["coverage_gate_passed"] = report["coverage_gate"]["passed"]
    _print(summary)
    if args.baseline and not report["coverage_gate"]["passed"]:
        raise SystemExit(1)


def cmd_parity(args: argparse.Namespace) -> None:
    from eth_nl2sql.store.build import connect
    from eth_nl2sql.store.parity import check

    fixtures = cfg.ROOT / "tests" / "fixtures"
    explanations = json.loads(args.explanations.read_text()) if args.explanations else None
    with connect(args.store) as con:
        report = check(
            con,
            fixtures / "bq_gold_results.json",
            fixtures / "stage_a_witnesses.json",
            explanations=explanations,
        )
    cfg.write_json(args.out, report)
    _print({key: report[key] for key in ("gold_exact", "witness_row_counts", "passed")})
    if not report["passed"]:
        if report.get("reason"):
            print(report["reason"], file=sys.stderr)
        sys.exit(1)


def cmd_local_plan(args: argparse.Namespace) -> None:
    from eth_nl2sql.store.local import plan_local

    report = plan_local(args.directory)
    cfg.write_json(args.out, report)
    _print({"joins_ok": report["joins_ok"], "joins": report["joins"], "out": str(args.out)})
    if not report["joins_ok"]:
        sys.exit(1)


def cmd_supplements(args: argparse.Namespace) -> None:
    from eth_nl2sql.store.supplements import download, plan

    if args.command == "supplement-plan":
        report = plan(args.project, args.directory)
        cfg.write_json(args.out, report)
        _print(report)
    else:
        report = download(args.project, args.directory, args.supplements, storage_api=not args.rest)
        _print({"tables": {k: v["rows"] for k, v in report["files"].items()}})


def cmd_prepare_local(args: argparse.Namespace) -> None:
    from eth_nl2sql.store.local import prepare_local

    report = prepare_local(args.directory, args.parquet, args.supplements)
    _print(
        {
            "scope": report["scope"],
            "complete_snapshot": False,
            "tables": {row["table"]: row["rows"] for row in report["files"]},
        }
    )


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
        if not path.is_file():
            continue
        for sql in sorted({row["sql"] for row in cfg.read_jsonl(path)}):
            total += 1
            try:
                execute(con, sql)
            except (ValidationError, ExecutionError) as exc:
                failures.append({"split": split, "code": exc.code, "error": str(exc), "sql": sql})
    _print({"checked": total, "failures": failures})
    if failures:
        sys.exit(1)


def cmd_build_entity_data(args: argparse.Namespace) -> None:
    from eth_nl2sql.data.entities import build_entity_data

    _print(build_entity_data(args.data, args.dictionary)["generated"])


def cmd_check_dataset(args: argparse.Namespace) -> None:
    from eth_nl2sql.data.dataset_audit import audit_dataset, render_audit
    from eth_nl2sql.store.build import connect

    protected = {args.store.resolve()}
    protected.update(p.resolve() for p in args.data.rglob("*") if p.is_file())
    protected.update(p.resolve() for p in args.dictionary.rglob("*") if p.is_file())
    if args.out.resolve() in protected or args.report.resolve() in protected:
        raise SystemExit("Dataset reports must not overwrite data, dictionary or store")
    if args.out.resolve() == args.report.resolve():
        raise SystemExit("JSON and Markdown report paths must be different")
    with connect(args.store) as con:
        report = audit_dataset(
            con,
            args.data,
            args.dictionary,
            progress=lambda message: print(message, file=sys.stderr),
        )
    cfg.write_json(args.out, report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(render_audit(report))
    _print(
        {
            "passed": report["passed"],
            "dev_eval_subsets": report["dev_eval_subsets"],
            "specifics": report["specifics"],
            "out": str(args.out),
        }
    )
    if not report["passed"]:
        sys.exit(1)


def cmd_check_annotations(args: argparse.Namespace) -> None:
    from eth_nl2sql.data.annotations import audit_annotations
    from eth_nl2sql.linking.dictionary import load_dictionary

    try:
        report = audit_annotations(
            cfg.read_jsonl(args.cases),
            cfg.read_jsonl(args.annotations),
            cfg.read_jsonl(args.reviews),
            load_dictionary(args.dictionary),
        )
    except (OSError, ValueError) as exc:
        report = {"passed": False, "issues": [str(exc)], "human_review_complete": False}
    _write_benchmark_report(args, report, [args.cases, args.annotations, args.reviews])
    if not report["passed"] or (args.require_human and not report["human_review_complete"]):
        raise SystemExit(1)


def _write_benchmark_report(args: argparse.Namespace, report: dict, inputs: list[Path]) -> None:
    protected = {p.resolve() for p in inputs}
    protected.update(p.resolve() for p in args.dictionary.rglob("*") if p.is_file())
    protected.update(p.resolve() for p in cfg.DATA_DIR.rglob("*") if p.is_file())
    if getattr(args, "store", None):
        protected.add(args.store.resolve())
    if args.out.resolve() in protected:
        raise SystemExit("Benchmark report must not overwrite input data, dictionary or store")
    cfg.write_json(args.out, report)
    _print(
        {
            k: v
            for k, v in report.items()
            if k
            not in {
                "cases",
                "gold",
                "annotations",
                "leakage",
                "details",
                "annotation_audit",
                "prediction_metadata",
            }
        }
    )


def cmd_check_benchmark(args: argparse.Namespace) -> None:
    from eth_nl2sql.data.benchmark import audit_benchmark
    from eth_nl2sql.store.build import connect

    if args.skip_execution:
        report = audit_benchmark(args.benchmark, args.data, args.dictionary)
    else:
        with connect(args.store, read_only=True) as con:
            report = audit_benchmark(args.benchmark, args.data, args.dictionary, con)
    inputs = [p for p in args.benchmark.rglob("*") if p.is_file()]
    inputs.extend(p for p in args.data.rglob("*") if p.is_file())
    _write_benchmark_report(args, report, inputs)
    if not report["passed"] or (args.require_release and not report["release_ready"]):
        raise SystemExit(1)


def cmd_freeze_benchmark(args: argparse.Namespace) -> None:
    from eth_nl2sql.data.benchmark import freeze_benchmark
    from eth_nl2sql.store.build import connect

    with connect(args.store, read_only=True) as con:
        try:
            manifest = freeze_benchmark(args.benchmark, args.data, args.dictionary, con)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
    _print(manifest)


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


def _linking_pipeline(dictionary_dir: Path, *, use_encoder: bool, variant: str = "full"):
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
        dictionary,
        SchemaLinker(catalog, synonyms, encoder),
        EntityLinker(dictionary, encoder),
        variant=variant,
    )


def _linking_path(split: str, variant: str = "full") -> Path:
    directory = cfg.DATA_DIR / "linking"
    return directory / (f"{split}.jsonl" if variant == "full" else f"{variant}/{split}.jsonl")


def _linking_provenance(dictionary: Path, use_encoder: bool) -> dict:
    return {
        "dictionary": {p.name: cfg.sha256_file(p) for p in sorted(dictionary.glob("*.json"))},
        "catalog_sha256": cfg.sha256_file(cfg.CATALOG_PATH),
        "synonyms_sha256": cfg.sha256_file(cfg.SYNONYMS_PATH),
        "encoder": cfg.load()["models"]["encoder"] if use_encoder else None,
        "code": {
            p.name: cfg.sha256_file(p)
            for p in sorted((cfg.ROOT / "src/eth_nl2sql/linking").glob("*.py"))
        },
    }


def _save_linkings(split: str, variant: str, rows: list[dict], provenance: dict) -> Path:
    path = _linking_path(split, variant)
    cfg.write_jsonl(path, rows)
    cfg.write_json(
        path.with_suffix(".manifest.json"),
        {
            **provenance,
            "split": split,
            "variant": variant,
            "predictions_sha256": cfg.sha256_file(path),
        },
    )
    return path


def _check_linking_manifest(path: Path, split: str, variant: str, dictionary: Path) -> dict:
    manifest_path = path.with_suffix(".manifest.json")
    if not manifest_path.exists():
        raise SystemExit(f"Missing linking manifest {manifest_path}; rerun link")
    manifest = json.loads(manifest_path.read_text())
    current = _linking_provenance(dictionary, use_encoder=False)
    if (
        any(
            manifest.get(k) != current[k]
            for k in ("dictionary", "catalog_sha256", "synonyms_sha256")
        )
        or manifest.get("predictions_sha256") != cfg.sha256_file(path)
        or any(manifest.get(k) != value for k, value in (("split", split), ("variant", variant)))
    ):
        raise SystemExit(f"Stale linking manifest/dictionary/schema in {path}; rerun link")
    return manifest


def cmd_link(args: argparse.Namespace) -> None:
    from eth_nl2sql.linking.context import LinkingPipeline, link_rows
    from eth_nl2sql.linking.variants import VARIANTS

    cases = _read_split(args.split, args.dictionary)
    pipeline = _linking_pipeline(args.dictionary, use_encoder=not args.no_encoder)
    provenance = _linking_provenance(args.dictionary, not args.no_encoder)
    outputs = {}
    for variant in VARIANTS if args.variant == "all" else (args.variant,):
        selected = LinkingPipeline(
            pipeline.entity.dictionary, pipeline.schema, pipeline.entity, variant=variant
        )
        rows = link_rows(selected, cases)
        outputs[variant] = str(_save_linkings(args.split, variant, rows, provenance))
    _print({"split": args.split, "rows": len(cases), "outputs": outputs})


def _load_linkings(split: str, variant: str = "full", cases: list[dict] | None = None) -> dict:
    from eth_nl2sql.linking.context import Linking

    path = _linking_path(split, variant)
    if not path.exists():
        raise SystemExit(f"missing {path}; run `eth-nl2sql link --split {split}` first")
    rows = cfg.read_jsonl(path)
    if len({row["id"] for row in rows}) != len(rows):
        raise SystemExit(f"Duplicate linking IDs in {path}")
    if cases is not None:
        questions = {c["id"]: c["question"] for c in cases}
        if {r["id"]: r.get("question") for r in rows} != questions:
            raise SystemExit(f"Stale linking questions/IDs in {path}; rerun link")
    if path.with_suffix(".manifest.json").exists():
        _check_linking_manifest(path, split, variant, cfg.DICTIONARY_DIR)
    return {row["id"]: Linking.from_json(row["linking"]) for row in rows}


def cmd_link_experiments(args: argparse.Namespace) -> None:
    from dataclasses import asdict

    from eth_nl2sql.generation.runs import prompt_suite
    from eth_nl2sql.linking.context import Linking, LinkingPipeline, link_rows
    from eth_nl2sql.linking.variants import EXPERIMENTS, VARIANTS

    cases = _read_split(args.split, args.dictionary)
    base = _linking_pipeline(args.dictionary, use_encoder=not args.no_encoder)
    provenance = _linking_provenance(args.dictionary, not args.no_encoder)
    linkings = {}
    for variant in VARIANTS:
        pipeline = LinkingPipeline(
            base.entity.dictionary, base.schema, base.entity, variant=variant
        )
        rows = link_rows(pipeline, cases)
        _save_linkings(args.split, variant, rows, provenance)
        linkings[variant] = {row["id"]: Linking.from_json(row["linking"]) for row in rows}
    train = _read_split("train")
    if args.examples:
        from eth_nl2sql.generation.retrieval import normalize_question

        example_rows = cfg.read_jsonl(args.examples)
        selected = {row["id"]: row["example_ids"] for row in example_rows}
        if len(selected) != len(example_rows) or set(selected) != {c["id"] for c in cases}:
            raise SystemExit("Example cache must cover exactly the split IDs, without duplicates")
        train_index = {row["id"]: row for row in train}
        examples = {}
        for case in cases:
            ids = selected[case["id"]]
            if len(ids) != 5 or len(set(ids)) != 5 or not set(ids) <= train_index.keys():
                raise SystemExit("Example cache needs five distinct training IDs per question")
            shots = [train_index[key] for key in ids]
            if any(
                (case.get("family_id") is not None and shot.get("family_id") == case["family_id"])
                or normalize_question(shot["question"]) == normalize_question(case["question"])
                for shot in shots
            ):
                raise SystemExit("Example cache leaks the question or its family")
            examples[case["id"]] = shots

        def retrieve(case):
            return examples[case["id"]]
    else:
        from eth_nl2sql.generation.retrieval import FewShotRetriever, load_encoder

        encoder = base.schema.encoder
        retriever = FewShotRetriever(
            train, encoder if encoder is not None else load_encoder(cfg.load()), k=5
        )

        def retrieve(case):
            return retriever.retrieve(case["question"], exclude_family=case.get("family_id"))

    suite = prompt_suite(
        cases,
        catalog=json.loads(cfg.CATALOG_PATH.read_text()),
        linkings=linkings,
        retrieve=retrieve,
    )
    outputs = {}
    for name, rows in suite.items():
        path = RUNS_DIR / name / f"prompts-{args.split}.jsonl"
        cfg.write_jsonl(path, rows)
        outputs[name] = cfg.sha256_file(path)
    cache = RUNS_DIR / f"linking-examples-{args.split}.jsonl"
    cfg.write_jsonl(cache, [{"id": r["id"], "example_ids": r["example_ids"]} for r in suite["b2"]])
    cfg.write_json(
        RUNS_DIR / f"linking-experiments-{args.split}.json",
        {
            **provenance,
            "split": args.split,
            "interventions": {k: asdict(v) for k, v in VARIANTS.items()},
            "configs": {"b2": None, **EXPERIMENTS},
            "prompts_sha256": outputs,
            "examples_sha256": cfg.sha256_file(cache),
            "train_sha256": cfg.sha256_file(SPLITS["train"]),
            "experiment_sha256": cfg.sha256_file(cfg.CONFIG_PATH),
            "generator": cfg.load()["models"]["generator"],
            "generation": cfg.load()["generation"],
            "store": str(cfg.STORE_PATH),
        },
    )
    _print({"split": args.split, "configs": list(suite), "examples": str(cache)})


def cmd_evaluate_linking(args: argparse.Namespace) -> None:
    from eth_nl2sql.data.annotations import audit_annotations
    from eth_nl2sql.linking.dictionary import load_dictionary
    from eth_nl2sql.linking.evaluate import score_predictions

    cases = _read_split(args.split, args.dictionary)
    directory = SPLITS["test"].parent if args.split == "test" else cfg.DATA_DIR
    prefix = "" if args.split == "test" else f"{args.split}-"
    annotations_path = directory / f"{prefix}annotations.jsonl"
    reviews_path = directory / (
        "reviews.jsonl" if args.split == "test" else f"{prefix}annotation-reviews.jsonl"
    )
    annotations = cfg.read_jsonl(annotations_path)
    reviews = cfg.read_jsonl(reviews_path)
    audit = audit_annotations(cases, annotations, reviews, load_dictionary(args.dictionary))
    if not audit["passed"]:
        raise SystemExit(f"Invalid linking annotations/reviews: {audit}")
    predictions_path = args.predictions or _linking_path(args.split, args.variant)
    predictions = cfg.read_jsonl(predictions_path)
    questions = {c["id"]: c["question"] for c in cases}
    if any(
        row.get("question") != questions.get(row["id"])
        or row.get("linking", {}).get("variant") != args.variant
        for row in predictions
    ):
        raise SystemExit("Stale linking questions or wrong prediction variant")
    metadata = _check_linking_manifest(predictions_path, args.split, args.variant, args.dictionary)
    try:
        report = score_predictions(
            predictions,
            annotations,
            split=args.split,
            human_review_complete=audit["human_review_complete"],
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    report.update(
        variant=args.variant,
        annotation_audit=audit,
        prediction_metadata=metadata,
        scorer_sha256=cfg.sha256_file(cfg.ROOT / "src/eth_nl2sql/linking/evaluate.py"),
        inputs_sha256={
            p.name: cfg.sha256_file(p) for p in (predictions_path, annotations_path, reviews_path)
        },
    )
    if args.out is None:
        args.out = cfg.ROOT / "reports/linking" / f"{args.variant}-{args.split}.json"
    _write_benchmark_report(args, report, [predictions_path, annotations_path, reviews_path])


def cmd_prompts(args: argparse.Namespace) -> None:
    from eth_nl2sql.generation.runs import CONFIGS, prompt_rows, training_rows

    if args.split == "test":
        _read_split(args.split)
    run = CONFIGS[args.config]
    catalog = json.loads(cfg.CATALOG_PATH.read_text())
    out_dir = RUNS_DIR / run.name
    if args.training:
        for split in ("train", "dev"):
            cases = _read_split(split)
            linkings = _load_linkings(split, run.linking_variant, cases) if run.linking else None
            rows = training_rows(run, cases, catalog=catalog, linkings=linkings)
            cfg.write_jsonl(out_dir / f"sft-{split}.jsonl", rows)
        _print({"config": run.name, "out": str(out_dir)})
        return
    cases = _read_split(args.split)
    retrieve = None
    if run.examples:
        from eth_nl2sql.generation.retrieval import FewShotRetriever, load_encoder

        experiment = cfg.load()
        retriever = FewShotRetriever(
            _read_split("train"),
            load_encoder(experiment),
            k=experiment["retrieval"]["examples"],
        )

        def retrieve(case):
            return retriever.retrieve(case["question"], exclude_family=case.get("family_id"))

    rows = prompt_rows(
        run,
        cases,
        catalog=catalog,
        linkings=_load_linkings(args.split, run.linking_variant, cases) if run.linking else None,
        retrieve=retrieve,
    )
    out = out_dir / f"prompts-{args.split}.jsonl"
    cfg.write_jsonl(out, rows)
    _print({"config": run.name, "split": args.split, "rows": len(rows), "out": str(out)})


def _adapter_path(name: str, out_dir: Path, requested: Path | None = None) -> Path | None:
    from eth_nl2sql.generation.runs import CONFIGS

    if not CONFIGS[name].fine_tuned:
        if requested is not None:
            raise ValueError(f"{name} must run without an adapter")
        return None
    expected = out_dir / "adapter"
    if requested is not None and requested.resolve() != expected.resolve():
        raise ValueError(f"{name} requires the adapter for this seed: {expected}")
    return expected


def cmd_preflight(args: argparse.Namespace) -> None:
    from eth_nl2sql.experiments import (
        checked_rows,
        model_digest,
        run_directory,
        selected_seeds,
        training_provenance,
    )
    from eth_nl2sql.generation.backend import (
        HuggingFaceGenerationBackend,
        preflight_generation,
    )
    from eth_nl2sql.train_qlora import preflight_training, training_inputs

    # The draft gate runs before tokenizer loading, including --training with --split test.
    _read_split(args.split)
    experiment = cfg.load()
    model_digest(experiment)
    inputs = RUNS_DIR / args.config
    for seed in selected_seeds(args.seed, experiment):
        out_dir = run_directory(RUNS_DIR, args.config, seed)
        if args.training:
            training_inputs(inputs / "sft-train.jsonl", inputs / "sft-dev.jsonl", experiment)
            provenance = training_provenance(
                inputs / "sft-train.jsonl",
                inputs / "sft-dev.jsonl",
                experiment,
                args.config,
                seed,
            )
        else:
            rows = checked_rows(inputs / f"prompts-{args.split}.jsonl")
            if any(row.get("config") != args.config for row in rows):
                raise ValueError("Wrong prompt configuration")
        backend = HuggingFaceGenerationBackend()
        backend.seed(seed if args.training else experiment["generation"]["seed"])
        tokenizer = backend.tokenizer(experiment)
        if args.training:
            _, _, report = preflight_training(
                inputs / "sft-train.jsonl",
                inputs / "sft-dev.jsonl",
                experiment,
                tokenizer=tokenizer,
                out=out_dir / "preflight-training.json",
            )
            report["provenance"] = provenance
            path = out_dir / "preflight-training.json"
        else:
            report = preflight_generation(rows, tokenizer, experiment)
            path = out_dir / f"preflight-predictions-{args.split}.json"
        cfg.write_json(path, report)
        _print({"config": args.config, "seed": seed, "report": path, **report})
        if not report["passed"]:
            raise SystemExit(1)


def cmd_generate(args: argparse.Namespace) -> None:
    from eth_nl2sql.experiments import run_directory, selected_seeds
    from eth_nl2sql.generation.backend import generate_file

    _read_split(args.split)
    experiment = cfg.load()
    for seed in selected_seeds(args.seed, experiment):
        out_dir = run_directory(RUNS_DIR, args.config, seed)
        adapter = _adapter_path(args.config, out_dir, args.adapter)
        written = generate_file(
            RUNS_DIR / args.config / f"prompts-{args.split}.jsonl",
            out_dir / f"predictions-{args.split}.jsonl",
            experiment,
            adapter=adapter,
            limit=args.limit,
            name=args.config,
            seed=seed,
        )
        _print({"config": args.config, "seed": seed, "generated": written, "out": out_dir})


def cmd_train(args: argparse.Namespace) -> None:
    from eth_nl2sql.experiments import run_directory, selected_seeds
    from eth_nl2sql.train_qlora import train, training_inputs

    experiment = cfg.load()
    names = ("b3", "b3l") if args.config == "all" else (args.config,)
    # Validate both real splits before loading any GPU model.
    for split in ("train", "dev"):
        _read_split(split)
    for name in names:
        inputs = RUNS_DIR / name
        training_inputs(inputs / "sft-train.jsonl", inputs / "sft-dev.jsonl", experiment)
    for name in names:
        inputs = RUNS_DIR / name
        for seed in selected_seeds(args.seed, experiment):
            out_dir = run_directory(RUNS_DIR, name, seed)
            summary = train(
                inputs / "sft-train.jsonl",
                inputs / "sft-dev.jsonl",
                out_dir,
                experiment,
                name=name,
                seed=seed,
                resume=args.resume,
            )
            _print({k: v for k, v in summary.items() if k not in ("log_history", "preflight")})


def cmd_echo_gold(args: argparse.Namespace) -> None:
    rows = [
        {"id": row["id"], "config": "gold-echo", "raw_output": row["sql"], "latency_ms": None}
        for row in _read_split(args.split)
    ]
    cfg.write_jsonl(RUNS_DIR / "gold-echo" / f"predictions-{args.split}.jsonl", rows)
    _print({"rows": len(rows)})


def cmd_evaluate(args: argparse.Namespace) -> None:
    from eth_nl2sql.evaluate import case_rows, evaluate_predictions, summarize
    from eth_nl2sql.experiments import (
        checked_rows,
        digest,
        generation_provenance,
        prediction_manifest,
        run_directory,
        selected_seeds,
        verify_predictions,
        write_manifest,
    )
    from eth_nl2sql.store.build import connect
    from eth_nl2sql.store.manifest import store_profile

    # Check the release gate before touching predictions or model artifacts.
    cases = _read_split(args.split)
    experiment = cfg.load()
    settings = experiment["evaluation"]
    seeds = (None,) if args.config == "gold-echo" else selected_seeds(args.seed, experiment)
    for seed in seeds:
        out_dir = (
            RUNS_DIR / args.config if seed is None else run_directory(RUNS_DIR, args.config, seed)
        )
        predictions_path = out_dir / f"predictions-{args.split}.jsonl"
        provenance = None
        if seed is not None:
            prompts_path = RUNS_DIR / args.config / f"prompts-{args.split}.jsonl"
            prompts = checked_rows(prompts_path)
            if {r["id"] for r in prompts} != {c["id"] for c in cases}:
                raise ValueError("Prompt IDs differ from the evaluation split")
            provenance = generation_provenance(
                prompts_path, experiment, args.config, seed, _adapter_path(args.config, out_dir)
            )
            verify_predictions(predictions_path, prompts, provenance)
        rows = cfg.read_jsonl(predictions_path)
        predictions = {row["id"]: row for row in rows}
        if len(predictions) != len(rows) or set(predictions) - {c["id"] for c in cases}:
            raise ValueError("Duplicate or unknown prediction IDs")
        with connect(args.store) as con:
            profile = store_profile(con)
            if args.split == "test":
                manifest = json.loads((SPLITS["test"].parent / "manifest.json").read_text())
                if profile != manifest["store"]:
                    raise SystemExit("Evaluation store differs from the frozen benchmark store")
            results = evaluate_predictions(
                con,
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
                "store": profile,
                "config": args.config,
                "seed": seed,
                "split": args.split,
                "missing_predictions": sorted({c["id"] for c in cases} - set(predictions)),
                "predictions_sha256": cfg.sha256_file(predictions_path),
                "dataset_sha256": cfg.sha256_file(SPLITS[args.split]),
                "case_ids_sha256": digest(sorted(c["id"] for c in cases)),
                "evaluation_settings_sha256": digest(settings),
                "evaluation_role": "final_benchmark" if args.split == "test" else "development",
            }
        )
        if provenance is not None:
            summary.update(
                {
                    k: provenance[k]
                    for k in (
                        "model_sha256",
                        "prompts_sha256",
                        "adapter_sha256",
                        "generation_sha256",
                    )
                }
            )
            summary["prediction_manifest_sha256"] = cfg.sha256_file(
                prediction_manifest(predictions_path)
            )
            training_manifest = out_dir / "training-manifest.json"
            if training_manifest.exists():
                training = json.loads(training_manifest.read_text())["provenance"]
                summary["training_protocol_sha256"] = digest(
                    {k: v for k, v in training.items() if k != "seed"}
                )
        if args.split == "test":
            summary["benchmark_manifest_sha256"] = cfg.sha256_file(
                SPLITS["test"].parent / "manifest.json"
            )
        cases_path = out_dir / f"cases-{args.split}.jsonl"
        evaluation_path = out_dir / f"eval-{args.split}.json"
        cfg.write_jsonl(cases_path, case_rows(results))
        cfg.write_json(evaluation_path, summary)
        write_manifest(
            evaluation_path.with_suffix(".manifest.json"),
            summary,
            evaluation_sha256=cfg.sha256_file(evaluation_path),
            cases_sha256=cfg.sha256_file(cases_path),
        )
        _print(
            {
                k: summary[k]
                for k in (
                    "config",
                    "seed",
                    "execution_accuracy",
                    "execution_accuracy_ci95",
                    "valid_sql_rate",
                )
            }
        )


def cmd_report(args: argparse.Namespace) -> None:
    from eth_nl2sql.report import write_report

    _read_split(args.split)
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
        command.add_argument(
            "--parquet", type=Path, default=cfg.DATA_DIR / "store" / "full-parquet"
        )
        command.add_argument("--location", default="US")
        command.add_argument(
            "--budget-bytes",
            type=int,
            help="cumulative cap; defaults to remaining free monthly quota",
        )
        command.add_argument(
            "--out",
            type=Path,
            default=cfg.ROOT
            / "reports"
            / "snapshot-t06"
            / ("dry-run.json" if name == "snapshot-plan" else "extraction.json"),
        )
        if name == "snapshot-run":
            command.add_argument(
                "--storage-api",
                action="store_true",
                help="use bounded Storage API streams instead of REST",
            )

    command = add(
        "snapshot-validate",
        cmd_snapshot_validate,
        "verify the full manifest, keys, date bounds and raw-table joins",
    )
    command.add_argument("--parquet", type=Path, default=cfg.DATA_DIR / "store" / "full-parquet")
    command.add_argument(
        "--out", type=Path, default=cfg.ROOT / "reports" / "snapshot-t06" / "data-quality.json"
    )

    command = add("build-store", cmd_build_store, "build the DuckDB store from parquet")
    command.add_argument("--parquet", type=Path, default=cfg.PARQUET_DIR)
    command.add_argument("--labels", type=Path, default=cfg.DICTIONARY_DIR)
    command.add_argument("--store", type=Path, default=cfg.STORE_PATH)

    command = add("check-dictionary", cmd_check_dictionary, "validate labels, aliases and concepts")
    command.add_argument("--dictionary", type=Path, default=cfg.DICTIONARY_DIR)

    command = add("build-entity-data", cmd_build_entity_data, "render entity train/dev templates")
    command.add_argument("--data", type=Path, default=cfg.DATA_DIR)
    command.add_argument("--dictionary", type=Path, default=cfg.DICTIONARY_DIR)

    command = add("check-dataset", cmd_check_dataset, "execute golds and audit splits/review")
    command.add_argument("--data", type=Path, default=cfg.DATA_DIR)
    command.add_argument("--dictionary", type=Path, default=cfg.DICTIONARY_DIR)
    command.add_argument("--store", type=Path, default=cfg.STORE_PATH)
    command.add_argument(
        "--out", type=Path, default=cfg.ROOT / "reports" / "entity-dataset" / "validation.json"
    )
    command.add_argument(
        "--report", type=Path, default=cfg.ROOT / "reports" / "entity-dataset" / "validation.md"
    )

    command = add(
        "check-annotations", cmd_check_annotations, "validate linking gold and review hashes"
    )
    command.add_argument("--cases", type=Path, default=cfg.DATA_DIR / "dev_eval.jsonl")
    command.add_argument(
        "--annotations", type=Path, default=cfg.DATA_DIR / "dev_eval-annotations.jsonl"
    )
    command.add_argument(
        "--reviews", type=Path, default=cfg.DATA_DIR / "dev_eval-annotation-reviews.jsonl"
    )
    command.add_argument("--dictionary", type=Path, default=cfg.DICTIONARY_DIR)
    command.add_argument("--require-human", action="store_true")
    command.add_argument(
        "--out", type=Path, default=cfg.ROOT / "reports" / "benchmark-t07" / "annotations.json"
    )

    for name, handler in (
        ("check-benchmark", cmd_check_benchmark),
        ("freeze-benchmark", cmd_freeze_benchmark),
    ):
        command = add(name, handler, "validate or freeze the separately versioned final benchmark")
        command.add_argument("--benchmark", type=Path, default=cfg.DATA_DIR / "benchmark" / "v2")
        command.add_argument("--data", type=Path, default=cfg.DATA_DIR)
        command.add_argument("--dictionary", type=Path, default=cfg.DICTIONARY_DIR)
        command.add_argument("--store", type=Path, default=cfg.STORE_PATH)
        if name == "check-benchmark":
            command.add_argument("--skip-execution", action="store_true")
            command.add_argument("--require-release", action="store_true")
            command.add_argument(
                "--out",
                type=Path,
                default=cfg.ROOT / "reports" / "benchmark-t07" / "benchmark.json",
            )

    command = add(
        "dictionary-coverage", cmd_dictionary_coverage, "measure dictionary presence in local data"
    )
    command.add_argument("--dictionary", type=Path, default=cfg.DICTIONARY_DIR)
    command.add_argument("--store", type=Path, default=cfg.STORE_PATH)
    command.add_argument(
        "--out", type=Path, default=cfg.ROOT / "reports" / "dictionary-v2" / "coverage.json"
    )
    command.add_argument(
        "--report", type=Path, default=cfg.ROOT / "reports" / "dictionary-v2" / "coverage.md"
    )
    command.add_argument(
        "--baseline",
        type=Path,
        help="require full scope, matching labels and no activity coverage loss",
    )

    command = add("local-plan", cmd_local_plan, "audit CSV joins and plan local enrichment")
    command.add_argument("--directory", type=Path, default=cfg.DATA_DIR / "raw" / "luanvan")
    command.add_argument(
        "--out", type=Path, default=cfg.ROOT / "reports" / "local-store" / "plan.json"
    )

    for name in ("supplement-plan", "supplement-run"):
        command = add(name, cmd_supplements, "dry-run or download missing local CSV attributes")
        command.add_argument("--project", required=True)
        command.add_argument("--directory", type=Path, default=cfg.DATA_DIR / "raw" / "luanvan")
        command.add_argument(
            "--rest", action="store_true", help="download via REST if Storage API is unavailable"
        )
        command.add_argument(
            "--supplements", type=Path, default=cfg.DATA_DIR / "store" / "supplements"
        )
        command.add_argument(
            "--out",
            type=Path,
            default=cfg.ROOT / "reports" / "local-store" / "supplement-plan.json",
        )

    command = add(
        "prepare-local", cmd_prepare_local, "enrich CSVs and export verified subset Parquet"
    )
    command.add_argument("--directory", type=Path, default=cfg.DATA_DIR / "raw" / "luanvan")
    command.add_argument("--supplements", type=Path, default=cfg.DATA_DIR / "store" / "supplements")
    command.add_argument("--parquet", type=Path, default=cfg.PARQUET_DIR)

    command = add("parity", cmd_parity, "compare local results with BigQuery observations")
    command.add_argument("--store", type=Path, default=cfg.STORE_PATH)
    command.add_argument("--out", type=Path, default=RUNS_DIR / "parity.json")
    command.add_argument(
        "--explanations",
        type=Path,
        help="JSON mapping of gold:<sql_sha256>/witness:<id> to evidence",
    )

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
    command.add_argument("--dictionary", type=Path, default=cfg.DICTIONARY_DIR)
    command.add_argument("--no-encoder", action="store_true", help="lexical/fuzzy stages only")
    from eth_nl2sql.linking.variants import VARIANTS

    command.add_argument("--variant", choices=(*VARIANTS, "all"), default="full")

    command = add(
        "link-experiments",
        cmd_link_experiments,
        "prepare controlled five-shot baseline and ablation prompts",
    )
    command.add_argument("--split", choices=SPLITS, default="dev_eval")
    command.add_argument("--dictionary", type=Path, default=cfg.DICTIONARY_DIR)
    command.add_argument("--no-encoder", action="store_true")
    command.add_argument("--examples", type=Path, help="reuse a cache of five training example IDs")

    command = add("evaluate-linking", cmd_evaluate_linking, "score saved predictions against T07")
    command.add_argument("--split", choices=("dev_eval", "test"), default="dev_eval")
    command.add_argument("--variant", choices=VARIANTS, default="full")
    command.add_argument("--dictionary", type=Path, default=cfg.DICTIONARY_DIR)
    command.add_argument("--predictions", type=Path)
    command.add_argument("--out", type=Path)

    from eth_nl2sql.generation.runs import CONFIGS

    command = add("prompts", cmd_prompts, "render prompts (or SFT rows) for a configuration")
    command.add_argument("--config", choices=CONFIGS, required=True)
    command.add_argument("--split", choices=SPLITS, default="dev_eval")
    command.add_argument("--training", action="store_true", help="write SFT train/dev rows")

    command = add(
        "preflight", cmd_preflight, "validate inputs and tokenize without loading a model"
    )
    command.add_argument("--config", choices=CONFIGS, required=True)
    command.add_argument("--split", choices=SPLITS, default="dev_eval")
    command.add_argument("--training", action="store_true")
    command.add_argument("--seed", choices=("42", "43", "44", "all"), default="42")

    command = add("generate", cmd_generate, "generate SQL for rendered prompts (GPU)")
    command.add_argument("--config", required=True)
    command.add_argument("--split", choices=SPLITS, default="dev_eval")
    command.add_argument("--adapter", type=Path)
    command.add_argument("--limit", type=int)
    command.add_argument("--seed", choices=("42", "43", "44", "all"), default="42")

    command = add("train", cmd_train, "QLoRA fine-tuning for b3/b3l (GPU)")
    command.add_argument("--config", choices=("b3", "b3l", "all"), required=True)
    command.add_argument("--seed", choices=("42", "43", "44", "all"), default="42")
    command.add_argument("--resume", action="store_true")

    command = add("echo-gold", cmd_echo_gold, "write gold SQL as predictions (pipeline check)")
    command.add_argument("--split", choices=SPLITS, default="dev_eval")

    command = add("evaluate", cmd_evaluate, "score predictions on the local store")
    command.add_argument("--config", required=True)
    command.add_argument("--split", choices=SPLITS, default="dev_eval")
    command.add_argument("--store", type=Path, default=cfg.STORE_PATH)

    command.add_argument("--seed", choices=("42", "43", "44", "all"), default="42")

    command = add("report", cmd_report, "write RESULTS.md from evaluated runs")
    command.add_argument("--split", choices=SPLITS, default="dev_eval")

    args = parser.parse_args(argv)
    try:
        args.handler(args)
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
