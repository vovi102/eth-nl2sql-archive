"""Offline controlled experiment preparation and draft annotation scoring."""

import json

import pytest
from conftest import MINI_DICTIONARY, P

from eth_nl2sql import cli
from eth_nl2sql import config as cfg
from eth_nl2sql.data.annotations import draft_development_annotations, pending_review
from eth_nl2sql.linking.dictionary import load_dictionary
from eth_nl2sql.linking.variants import EXPERIMENTS, VARIANTS
from eth_nl2sql.linking.workflow import linking_path


@pytest.fixture()
def experiment(tmp_path, monkeypatch):
    case = {
        "id": "q1",
        "question": "Count transactions received by Binance.",
        "sql": f"SELECT COUNT(*) FROM `{P}.transaction_facts`"
        "(DATE '2026-06-01', DATE '2026-06-08')",
        "family_id": "evaluation",
        "entity_expectations": {
            "owners": ["Binance"],
            "direction": "to",
        },
    }
    train = [
        {
            "id": f"e{i}",
            "question": f"Training example {i}",
            "sql": f"SELECT {i}",
            "family_id": f"train-{i}",
        }
        for i in range(5)
    ]
    monkeypatch.setattr(cfg, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(cli, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(
        cli, "read_checked_split", lambda name, *args: train if name == "train" else [case]
    )
    train_path = cfg.DATA_DIR / "train.jsonl"
    cfg.write_jsonl(train_path, train)
    monkeypatch.setitem(cli.SPLITS, "train", train_path)
    annotations = draft_development_annotations([case], load_dictionary(MINI_DICTIONARY))
    cfg.write_jsonl(cfg.DATA_DIR / "dev_eval-annotations.jsonl", annotations)
    cfg.write_jsonl(
        cfg.DATA_DIR / "dev_eval-annotation-reviews.jsonl", [pending_review(case, annotations[0])]
    )
    cache = tmp_path / "examples.jsonl"
    cfg.write_jsonl(cache, [{"id": "q1", "example_ids": [r["id"] for r in train]}])
    return cache


def test_cli_suite_and_direct_scores_are_reproducible(experiment, tmp_path):
    args = [
        "link-experiments",
        "--split",
        "dev_eval",
        "--no-encoder",
        "--dictionary",
        str(MINI_DICTIONARY),
        "--examples",
        str(experiment),
    ]
    cli.main(args)
    files = [
        p
        for directory in (cfg.DATA_DIR / "linking", cli.RUNS_DIR)
        for p in directory.rglob("*")
        if p.is_file()
    ]
    before = {p: p.read_bytes() for p in files}
    cli.main(args)
    assert all(p.read_bytes() == value for p, value in before.items())
    manifest = json.loads((cli.RUNS_DIR / "linking-experiments-dev_eval.json").read_text())
    assert set(manifest["prompts_sha256"]) == {"b2", *EXPERIMENTS}
    assert set(manifest["interventions"]) == set(VARIANTS)
    report = tmp_path / "linking-score.json"
    cli.main(["evaluate-linking", "--dictionary", str(MINI_DICTIONARY), "--out", str(report)])
    result = json.loads(report.read_text())
    assert result["evaluation_scope"] == "development"
    assert result["metrics"]["entity"]["rate"] == 1
    assert not result["human_review_complete"]
    with pytest.raises(SystemExit, match="must not overwrite"):
        cli.main(
            [
                "evaluate-linking",
                "--dictionary",
                str(MINI_DICTIONARY),
                "--out",
                str(cfg.DATA_DIR / "dev_eval-annotations.jsonl"),
            ]
        )


def test_cli_rejects_a_changed_question_or_wrong_variant(experiment, tmp_path):
    cli.main(["link", "--split", "dev_eval", "--no-encoder", "--dictionary", str(MINI_DICTIONARY)])
    path = linking_path("dev_eval")
    rows = cfg.read_jsonl(path)
    rows[0]["question"] = "Some other question"
    cfg.write_jsonl(path, rows)
    with pytest.raises(SystemExit, match="Stale linking"):
        cli.main(
            [
                "evaluate-linking",
                "--dictionary",
                str(MINI_DICTIONARY),
                "--out",
                str(tmp_path / "score.json"),
            ]
        )


def test_suite_rejects_retrieval_examples_outside_train(experiment):
    cfg.write_jsonl(experiment, [{"id": "q1", "example_ids": ["gold"] * 5}])
    with pytest.raises(SystemExit, match="five distinct training IDs"):
        cli.main(
            [
                "link-experiments",
                "--no-encoder",
                "--dictionary",
                str(MINI_DICTIONARY),
                "--examples",
                str(experiment),
            ]
        )


def test_scoring_rejects_predictions_bound_to_a_different_dictionary(experiment, tmp_path):
    cli.main(["link", "--split", "dev_eval", "--no-encoder", "--dictionary", str(MINI_DICTIONARY)])
    path = linking_path("dev_eval").with_suffix(".manifest.json")
    manifest = json.loads(path.read_text())
    manifest["dictionary"]["entities.json"] = "0" * 64
    cfg.write_json(path, manifest)
    with pytest.raises(SystemExit, match="Stale linking manifest/dictionary/schema"):
        cli.main(
            [
                "evaluate-linking",
                "--dictionary",
                str(MINI_DICTIONARY),
                "--out",
                str(tmp_path / "score.json"),
            ]
        )
