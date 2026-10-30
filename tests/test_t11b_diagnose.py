"""Paired diagnostic prompts preserve the control and never change the source."""

import copy
import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

from eth_nl2sql.config import write_json, write_jsonl
from eth_nl2sql.generation.prompt import build_messages, messages_digest

spec = importlib.util.spec_from_file_location(
    "t11b_diagnose", Path(__file__).parents[1] / "scripts/t11b_diagnose.py"
)
diagnose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diagnose)


def test_prompt_factorial_preserves_question_and_does_not_mutate_original():
    catalog = {"analytical_relations": {"transaction_facts": {"fields": {"is_success": {}}}}}
    original = build_messages(
        "Count successful transactions in the first three days.", system="schema"
    )
    saved = copy.deepcopy(original)
    variants = {v: diagnose.variant_messages(original, v, catalog) for v in diagnose.VARIANTS}
    assert original == saved
    assert variants["original"] == original
    assert variants["dates"][0]["content"] == "schema" + diagnose.DATE_RULES
    assert (
        variants["dates-columns"][0]["content"]
        == variants["columns"][0]["content"] + diagnose.DATE_RULES
    )
    assert "is_success" in variants["columns"][0]["content"]
    assert all(messages[1] == original[1] for messages in variants.values())
    # Adapter and base take the same messages; model activation is the only difference.
    assert messages_digest(variants["dates-columns"]) == messages_digest(
        diagnose.variant_messages(saved, "dates-columns", catalog)
    )
    with pytest.raises(ValueError, match="Unknown"):
        diagnose.variant_messages(original, "other", catalog)


def test_diagnostic_evaluator_rejects_missing_reordered_or_changed_prompts(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "t11b_diagnose", diagnose)
    report_spec = importlib.util.spec_from_file_location(
        "t11b_diagnosis_report", Path(__file__).parents[1] / "scripts/t11b_diagnosis_report.py"
    )
    report = importlib.util.module_from_spec(report_spec)
    report_spec.loader.exec_module(report)
    prompts = [
        {"id": f"q{i}", "messages": build_messages(f"Q{i}", system="schema")} for i in range(100)
    ]
    rows = [{"id": r["id"], "prompt_sha256": messages_digest(r["messages"])} for r in prompts[:10]]
    path = tmp_path / "predictions.jsonl"
    write_jsonl(path, rows)
    assert report.checked_predictions(path, prompts) == rows
    write_jsonl(path, rows[:8])
    with pytest.raises(ValueError, match="Incomplete"):
        report.checked_predictions(path, prompts)
    write_jsonl(path, list(reversed(rows)))
    with pytest.raises(ValueError, match="reordered"):
        report.checked_predictions(path, prompts)
    write_jsonl(path, rows)
    prompts[0]["messages"][1]["content"] += " changed"
    with pytest.raises(ValueError, match="Prompt hash"):
        report.checked_predictions(path, prompts)


@pytest.mark.parametrize("changed_plan", [False, True])
def test_diagnostic_collection_binds_plan_and_retains_manifest(monkeypatch, tmp_path, changed_plan):
    monkeypatch.setitem(sys.modules, "t11b_diagnose", diagnose)
    report_spec = importlib.util.spec_from_file_location(
        "t11b_diagnosis_report", Path(__file__).parents[1] / "scripts/t11b_diagnosis_report.py"
    )
    report = importlib.util.module_from_spec(report_spec)
    report_spec.loader.exec_module(report)
    monkeypatch.setattr(report, "WORK", tmp_path / "diagnosis")
    expected = {"adapter_kernel": "producer/frozen"}
    write_json(report.WORK / "plan.json", expected)
    actual = {"adapter_kernel": "other/model"} if changed_plan else expected
    members = {"plan.json": json.dumps(actual).encode(), "prediction.jsonl": b"prediction"}
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in members.items()}
    archive = tmp_path / "transport.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        for name, data in members.items():
            bundle.writestr(name, data)
        bundle.writestr("manifest.json", json.dumps(manifest))
    if changed_plan:
        with pytest.raises(ValueError, match="submitted input"):
            report.collect(archive)
        assert not (report.WORK / "output").exists()
    else:
        report.collect(archive)
        assert (report.WORK / "output/prediction.jsonl").read_bytes() == b"prediction"
        assert json.loads((report.WORK / "output/manifest.json").read_text()) == manifest
        assert not list(report.WORK.rglob("*.zip"))
