"""The GPU smoke must reject SQL that static allowlisting accepts."""

import json

import pytest

from eth_nl2sql import config as cfg
from eth_nl2sql.generation.smoke import inspect_predictions, require_smoke_pass
from eth_nl2sql.validation import PROJECT_DATASET as P


def prediction(sql):
    return {"id": "q1", "raw_output": sql, "finish_reason": "stop"}


@pytest.mark.parametrize(
    "relation",
    [
        "transaction_facts",
        "block_facts",
        "token_transfer_facts",
        "labeled_transactions",
        "labeled_token_transfers",
        "contract_dimension",
    ],
)
def test_smoke_rejects_tvf_used_as_table(relation):
    report = inspect_predictions([prediction(f"SELECT COUNT(*) AS n FROM `{P}.{relation}`")])
    assert not report["passed"]
    assert report["cases"][0]["status"] == "compile_error"
    with pytest.raises(ValueError, match="smoke"):
        require_smoke_pass(report)


@pytest.mark.parametrize(
    "args,status",
    [
        ("", "window_invalid"),
        ("DATE '2026-06-01'", "window_invalid"),
        ("DATE '2026-06-01', DATE '2026-06-02', DATE '2026-06-03'", "window_invalid"),
        ("TIMESTAMP '2026-06-01 00:00:00', DATE '2026-06-02'", "window_invalid"),
        ("NULL, DATE '2026-06-02'", "window_invalid"),
        ("DATE '2026-06-02', DATE '2026-06-01'", "window_invalid"),
        ("DATE '2026-04-01', DATE '2026-04-02'", "window_outside_snapshot"),
    ],
)
def test_smoke_checks_tvf_arguments(args, status):
    report = inspect_predictions(
        [prediction(f"SELECT COUNT(*) AS n FROM `{P}.transaction_facts`({args})")]
    )
    assert not report["passed"]
    assert report["cases"][0]["status"] == status


def test_smoke_binds_columns_on_empty_schema():
    report = inspect_predictions(
        [
            prediction(
                f"SELECT invented_column FROM `{P}.transaction_facts`"
                "(DATE '2026-06-01', DATE '2026-06-02')"
            )
        ]
    )
    assert not report["passed"]
    assert report["cases"][0]["status"] == "compile_error"
    assert "invented_column" in report["cases"][0]["error"]


def test_smoke_accepts_all_real_signatures_without_data():
    catalog = json.loads(cfg.CATALOG_PATH.read_text())
    rows = []
    for name, relation in catalog["analytical_relations"].items():
        args = [
            "DATE '2026-06-01'" if p == "start_date" else "DATE '2026-06-02'"
            for p in relation.get("parameters", {})
        ]
        call = f"({', '.join(args)})" if args else ""
        rows.append({**prediction(f"SELECT COUNT(*) AS n FROM `{P}.{name}`{call}"), "id": name})
    report = inspect_predictions(rows)
    assert report["passed"]
    assert report["compile_passed"] == 8
    assert "execution_accuracy" not in report
    require_smoke_pass(report)


def test_original_smoke_is_now_rejected():
    rows = cfg.read_jsonl(cfg.ROOT / "reports/gpu-development-t11a/b3-base-smoke-10.jsonl")
    report = inspect_predictions(rows)
    assert not report["passed"]
    assert report["cases"][0]["status"] == "compile_error"


def test_empty_and_unextractable_outputs_cannot_pass():
    assert not inspect_predictions([])["passed"]
    report = inspect_predictions([prediction("I cannot answer this question.")])
    assert not report["passed"]
    assert report["cases"][0]["status"] == "no_sql"


def test_smoke_cli_writes_failure_report_before_exiting(tmp_path):
    from eth_nl2sql.cli import main

    predictions = tmp_path / "predictions.jsonl"
    out = tmp_path / "smoke.json"
    cfg.write_jsonl(predictions, [prediction(f"SELECT COUNT(*) AS n FROM `{P}.block_facts`")])
    with pytest.raises(SystemExit, match="smoke failed"):
        main(["smoke", "--predictions", str(predictions), "--out", str(out)])
    assert not json.loads(out.read_text())["passed"]


def test_gpu_runner_stops_before_resume_on_bad_smoke(monkeypatch, tmp_path):
    import importlib
    import sys
    from types import SimpleNamespace

    monkeypatch.syspath_prepend(str(cfg.ROOT / "scripts"))
    runner = importlib.import_module("t11a")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORT", tmp_path / "report")
    monkeypatch.setattr(runner, "verify_inputs", lambda: {})
    monkeypatch.setattr(runner, "verify_cache", lambda *_: {})
    for key in (
        "HF_HOME",
        "HF_HUB_CACHE",
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "TOKENIZERS_PARALLELISM",
    ):
        monkeypatch.setenv(key, "")
    monkeypatch.setitem(
        sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: True))
    )
    rows = [prediction(f"SELECT COUNT(*) AS n FROM `{P}.labeled_transactions`")]
    path = tmp_path / "runs/b3-base/seed-42/predictions-dev_eval.jsonl"
    cfg.write_jsonl(path, rows)
    monkeypatch.setattr(runner, "verify_run", lambda *_: (path, rows, {}))
    commands = []

    def invoke(argv, **kwargs):
        commands.append(argv)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(runner.subprocess, "run", invoke)
    with pytest.raises(ValueError, match="smoke failed"):
        runner.gpu(tmp_path / "cache", tmp_path / "pins.json")
    assert not any("--limit" not in command and "generate" in command for command in commands)
    report = json.loads((tmp_path / "report/b3-base-smoke-inspection.json").read_text())
    assert report["cases"][0]["status"] == "compile_error"
