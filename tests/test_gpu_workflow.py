"""GPU orchestration regressions, exercised without loading a model."""

import base64
import hashlib
import importlib
import json
import os
import subprocess
import sys
import zipfile
import zlib
from types import SimpleNamespace

import pytest

from eth_nl2sql import config as cfg
from eth_nl2sql.generation.runs import Job
from eth_nl2sql.gpu_workflow import StageRunner, archive_outputs, collect_outputs, package_inputs
from eth_nl2sql.kaggle import load_settings


@pytest.fixture()
def scripts(monkeypatch):
    monkeypatch.syspath_prepend(str(cfg.ROOT / "scripts"))
    return SimpleNamespace(
        runner=importlib.import_module("t11b"),
        a=importlib.import_module("t11a_notebook"),
        b=importlib.import_module("t11b_notebook"),
    )


@pytest.mark.parametrize("seed", [7, 42, 123])
def test_evaluate_preserves_the_entire_job_seed(scripts, monkeypatch, seed):
    class PredictionsReached(Exception):
        pass

    def predictions(name, actual_seed):
        assert (name, actual_seed) == ("b3", seed)
        raise PredictionsReached

    monkeypatch.setattr(scripts.runner, "prediction_rows", predictions)
    with pytest.raises(PredictionsReached):
        scripts.runner.evaluate(f"b3-seed-{seed}")


def test_notebook_build_is_repeatable_and_does_not_change_t11a(scripts, tmp_path, monkeypatch):
    # Restore the global after the test so the old implementation cannot pollute other tests.
    monkeypatch.setattr(scripts.a, "BOOTSTRAP", scripts.a.BOOTSTRAP)
    original = scripts.a.BOOTSTRAP
    archive = tmp_path / "inputs.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("example.txt", "payload")
    output = tmp_path / "notebook"
    snapshots = []
    for _ in range(2):
        scripts.b.build(archive, output, "tester/experiment", "b3-seed-42")
        snapshots.append({p.name: p.read_bytes() for p in output.iterdir()})
    assert snapshots[0] == snapshots[1]
    assert scripts.a.BOOTSTRAP == original
    metadata = json.loads((output / "kernel-metadata.json").read_text())
    assert metadata["code_file"] == "t11b.ipynb"
    source = json.loads((output / metadata["code_file"]).read_text())["cells"][0]["source"]
    assert source.count("zlib.decompress(payload)") == 1
    compile(source, metadata["code_file"], "exec")
    payload = {}
    exec("\n".join(source.splitlines()[:2]), payload)
    encoded = base64.b64decode(payload["PAYLOAD"])
    assert hashlib.sha256(encoded).hexdigest() == payload["BUNDLE_SHA256"]
    assert zlib.decompress(encoded) == archive.read_bytes()
    scripts.a.build(archive, tmp_path / "a", "tester/control")
    a_source = json.loads((tmp_path / "a/t11a.ipynb").read_text())["cells"][0]["source"]
    assert "zlib.decompress" not in a_source
    assert "scripts/t11a.py" in a_source


def test_t11b_requires_cuda_before_checking_model_cache(scripts, tmp_path, monkeypatch):
    runner = scripts.runner
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPORT", tmp_path / "reports/t11b")
    cfg.write_json(runner.REPORT / "inputs-manifest.json", {"files": {}})
    monkeypatch.setitem(
        sys.modules, "torch", SimpleNamespace(cuda=SimpleNamespace(is_available=lambda: False))
    )
    monkeypatch.setattr(
        runner, "verify_cache", lambda *_: pytest.fail("Cache read before CUDA guard")
    )
    for key in (
        "HF_HOME",
        "HF_HUB_CACHE",
        "HF_HUB_OFFLINE",
        "TRANSFORMERS_OFFLINE",
        "TOKENIZERS_PARALLELISM",
    ):
        monkeypatch.setenv(key, "")
    with pytest.raises(ValueError, match="requires an actual CUDA GPU"):
        runner.gpu("pilot", tmp_path / "cache")
    status = json.loads((runner.REPORT / "pilot/status.json").read_text())
    assert status["status"] == "failed"
    assert (tmp_path.parent / "t11b-pilot-artifacts.zip").is_file()


@pytest.mark.parametrize("script", ["t11a.py", "t11b.py"])
def test_gpu_cli_requires_home_before_starting(script, tmp_path):
    result = subprocess.run(
        [sys.executable, str(cfg.ROOT / "scripts" / script), "gpu"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "gpu requires --hf-home" in result.stderr
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "identifier",
    [
        "b3-seed--7",
        "b3-seed-x",
        "unknown-seed-42",
        "b1-seed-42",
        "b3-seed-42/../43",
    ],
)
def test_invalid_jobs_are_rejected(identifier):
    with pytest.raises(ValueError, match="Invalid development job"):
        Job.parse(identifier)


@pytest.mark.parametrize(
    "identifier,config,seed",
    [
        ("pilot", "b1", 42),
        ("b3-seed-7", "b3", 7),
        ("b3l-seed-123", "b3l", 123),
    ],
)
def test_job_roundtrip(identifier, config, seed):
    job = Job.parse(identifier)
    assert (job.config.name, job.seed) == (config, seed)
    assert job.identifier == identifier


def test_bundle_roundtrip_and_repeated_output_archive(tmp_path):
    root = tmp_path / "root"
    report = root / "reports/t11"
    inputs = root / "prompts.jsonl"
    cfg.write_jsonl(inputs, [{"id": "q1", "messages": []}])
    cfg.write_jsonl(
        root / "data/dev_eval.jsonl",
        [
            {
                "id": "q1",
                "question": "Count",
                "sql": "local gold",
                "answer": "local answer",
            }
        ],
    )
    bundle = tmp_path / "inputs.zip"
    manifest = package_inputs(root, report, bundle, [inputs], {"task": "test"})
    with zipfile.ZipFile(bundle) as archive:
        assert json.loads(archive.read("data/dev_eval.jsonl")) == {"id": "q1", "question": "Count"}
        for name, checksum in manifest["files"].items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == checksum
    output = tmp_path / "outputs.zip"
    for _ in range(2):
        archive_outputs(root, (report,), report / "outputs-manifest.json", output)
        target = tmp_path / "collected"
        observed = collect_outputs(
            target,
            output,
            "reports/t11/outputs-manifest.json",
            can_replace=lambda _: False,
        )
        assert "reports/t11/outputs-manifest.json" not in observed
        assert (target / "reports/t11/bundle.json").read_bytes() == (
            report / "bundle.json"
        ).read_bytes()


def test_t11b_collect_checks_every_file_before_writing(scripts, tmp_path, monkeypatch):
    runner = scripts.runner
    root = tmp_path / "root"
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "REPORT", root / "reports/gpu-development-t11b")
    archive = tmp_path / "bad.zip"
    first = "runs/b3/seed-42/first.txt"
    last = "runs/b3/seed-42/last.txt"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(first, "verified")
        bundle.writestr(last, "tampered")
        bundle.writestr(
            "reports/gpu-development-t11b/pilot/outputs-manifest.json",
            json.dumps(
                {
                    first: hashlib.sha256(b"verified").hexdigest(),
                    last: "0" * 64,
                }
            ),
        )
    with pytest.raises(ValueError, match="Artifact hash mismatch"):
        runner.collect("pilot", archive)
    assert not root.exists()


@pytest.mark.parametrize("stream", [False, True])
def test_failed_cli_stage_retains_logs_and_measurement(tmp_path, stream):
    runner = StageRunner(cfg.ROOT, tmp_path, dict(os.environ), stream=stream)
    with pytest.raises(RuntimeError, match="invalid failed"):
        runner("invalid", "unknown-command")
    stages = json.loads((tmp_path / "stages.json").read_text())
    assert stages[0]["returncode"] == 2
    assert stages[0]["runtime_s"] > 0
    assert "unknown-command" in (tmp_path / "invalid.log").read_text()


def test_kaggle_deployment_identity_is_configurable(tmp_path, monkeypatch):
    settings_file = tmp_path / "kaggle.toml"
    settings_file.write_text(
        'owner = "original"\nrun_tag = "experiment"\nenvironment_cache = "cache"\n'
    )
    for key in ("OWNER", "RUN_TAG", "ENVIRONMENT_CACHE"):
        monkeypatch.delenv(f"ETH_NL2SQL_KAGGLE_{key}", raising=False)
    settings = load_settings(settings_file)
    assert settings.kernel("t11b", "pilot") == "original/eth-nl2sql-t11b-pilot-experiment"
    monkeypatch.setenv("ETH_NL2SQL_KAGGLE_OWNER", "tester")
    monkeypatch.setenv("ETH_NL2SQL_KAGGLE_RUN_TAG", "new-run")
    monkeypatch.setenv("ETH_NL2SQL_KAGGLE_ENVIRONMENT_CACHE", "model-cache")
    settings = load_settings(settings_file)
    assert settings.kernel("t11a") == "tester/eth-nl2sql-t11a-new-run"
    assert settings.cache_kernel == "tester/model-cache"
