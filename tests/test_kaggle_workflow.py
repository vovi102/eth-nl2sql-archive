"""Readable notebook deployment: snapshots, input integrity, parity and CPU cache."""

import copy
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from eth_nl2sql import config as cfg
from eth_nl2sql.gpu_notebook import notebook_source
from eth_nl2sql.kaggle import KaggleClient
from eth_nl2sql.kaggle_workflow import build_workflows, local_status
from eth_nl2sql.model_cache import fetch_cache


@pytest.fixture()
def project(tmp_path):
    root = tmp_path / "project"
    (root / "configs").mkdir(parents=True)
    shutil.copyfile(cfg.ROOT / "configs/experiment.toml", root / "configs/experiment.toml")
    (root / "configs/kaggle.toml").write_text(
        'owner = "tester"\nenvironment_cache = "model-cache"\n'
    )
    for name in (
        "pyproject.toml",
        "uv.lock",
        "README.md",
        "src/example.py",
        "scripts/t11b.py",
        "scripts/model_cache.py",
    ):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# source\n")
    for name in (
        "data/train.jsonl",
        "data/dev.jsonl",
        "runs/b3/prompts-dev_eval.jsonl",
        "runs/b3/sft-train.jsonl",
        "runs/b3/sft-dev.jsonl",
    ):
        cfg.write_jsonl(root / name, [{"id": "q1"}])
    cfg.write_jsonl(
        root / "data/dev_eval.jsonl",
        [
            {"id": "q1", "question": "Question", "sql": "SECRET LOCAL GOLD"},
        ],
    )
    evidence = root / "reports/experiments/inputs-manifest.json"
    cfg.write_json(evidence, {"immutable": "accepted evidence"})
    output = root / ".cache/kaggle"
    return SimpleNamespace(root=root, output=output, evidence=evidence)


def test_build_is_deterministic_preserves_evidence_and_keeps_gold_local(project):
    before = project.evidence.read_bytes()
    build_workflows(project.root, project.output)
    first = {
        name: (project.root / f"notebooks/{name}.ipynb").read_bytes()
        for name in ("fine_tune", "model_cache")
    }
    build_workflows(project.root, project.output)
    assert project.evidence.read_bytes() == before
    for name, expected in first.items():
        deployment = project.output / name
        assert (project.root / f"notebooks/{name}.ipynb").read_bytes() == expected
        assert expected == (deployment / f"{name}.ipynb").read_bytes()
        assert len(expected) < 20_000
        assert b"PAYLOAD" not in expected
        assert local_status(project.root, deployment, name)["status"] == "current"
    metadata = json.loads((project.output / "model_cache/kernel-metadata.json").read_text())
    assert metadata["enable_gpu"] is False
    assert metadata["kernel_sources"] == []
    with zipfile.ZipFile(project.output / "inputs.bundle") as bundle:
        assert json.loads(bundle.read("data/dev_eval.jsonl")) == {
            "id": "q1",
            "question": "Question",
        }
        assert all(b"SECRET LOCAL GOLD" not in bundle.read(n) for n in bundle.namelist())
    (project.root / "src/example.py").write_text("# changed source\n")
    assert (
        local_status(project.root, project.output / "fine_tune", "fine_tune")["status"]
        == "needs_build"
    )
    (project.root / "src/new.py").write_text("# new source\n")
    assert (
        "src/new.py"
        in local_status(project.root, project.output / "fine_tune", "fine_tune")["changed"]
    )


def test_rendered_input_cell_rejects_tampering_before_extracting(project, tmp_path):
    build_workflows(project.root, project.output)
    deployment = project.output / "fine_tune"
    notebook = json.loads((deployment / "fine_tune.ipynb").read_text())
    state = {}
    exec(notebook["cells"][1]["source"], state)
    inputs = tmp_path / "input"
    inputs.mkdir()
    archive = inputs / state["INPUT_FILE"]
    shutil.copyfile(deployment / "inputs" / state["INPUT_FILE"], archive)
    target = tmp_path / "working"
    source = notebook["cells"][3]["source"]
    assert "Path('/kaggle/input')" in source
    assert "Path('/kaggle/working/eth-nl2sql')" in source
    source = source.replace("Path('/kaggle/input')", f"Path({str(inputs)!r})")
    source = source.replace("Path('/kaggle/working/eth-nl2sql')", f"Path({str(target)!r})")
    archive.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="checksum mismatch"):
        exec(source, state)
    assert not target.exists()
    shutil.copyfile(deployment / "inputs" / state["INPUT_FILE"], archive)
    exec(source, state)
    assert (target / "src/example.py").is_file()
    assert "sql" not in json.loads((target / "data/dev_eval.jsonl").read_text())


def test_sync_status_ignores_execution_output_and_never_pushes(project):
    build_workflows(project.root, project.output)
    deployment = project.output / "fine_tune"
    calls = []

    def execute(argv, **kwargs):
        calls.append(argv)
        if argv[1:3] == ["datasets", "files"]:
            record = json.loads((deployment / "deployment.json").read_text())
            return SimpleNamespace(
                returncode=0,
                stderr="",
                stdout=json.dumps({"datasetFiles": [{"name": record["input_file"]}]}),
            )
        assert argv[:3] == ["kaggle", "kernels", "pull"]
        target = Path(argv[argv.index("-p") + 1])
        metadata = json.loads((deployment / "kernel-metadata.json").read_text())
        cfg.write_json(target / "kernel-metadata.json", metadata)
        notebook = json.loads((deployment / metadata["code_file"]).read_text())
        notebook["cells"][1]["outputs"] = [{"output_type": "stream", "text": "GPU done"}]
        notebook["cells"][1]["source"] = notebook["cells"][1]["source"].splitlines(keepends=True)
        notebook["metadata"]["kaggle"] = {"extra": "server metadata"}
        cfg.write_json(target / metadata["code_file"], notebook)
        return SimpleNamespace(returncode=0, stderr="", stdout="Downloaded")

    client = KaggleClient(project.root, project.output / "logs", execute=execute)
    state = client.sync_status(deployment)
    assert state["status"] == "in_sync"
    assert state["input_file_available"] is True
    assert state["local_provenance"] == state["remote_provenance"]
    assert all("push" not in argv and "create" not in argv for argv in calls)
    sample = json.loads((deployment / "fine_tune.ipynb").read_text())
    different = copy.deepcopy(sample)
    different["cells"][-1]["source"] += "\nprint('changed code')\n"
    assert notebook_source(sample) != notebook_source(different)


def test_publishing_inputs_is_private_and_does_not_submit_a_notebook(project):
    build_workflows(project.root, project.output)
    calls = []

    def execute(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(returncode=0, stdout="Dataset submitted", stderr="")

    client = KaggleClient(project.root, project.output / "logs", execute=execute)
    deployment = project.output / "fine_tune"
    result = client.publish_inputs(deployment, create=True)
    assert result["status"] == "submitted"
    assert calls[0][:3] == ["kaggle", "datasets", "create"]
    assert "--public" not in calls[0]
    assert "--delete-old-versions" not in calls[0]
    assert client.publish_inputs(deployment, create=True) == result
    assert len(calls) == 1
    with zipfile.ZipFile(
        deployment
        / "inputs"
        / json.loads((deployment / "deployment.json").read_text())["input_file"],
        "a",
    ) as bundle:
        bundle.writestr("tampered.txt", "new bytes")
    with pytest.raises(ValueError, match="Staged inputs changed"):
        client.publish_inputs(deployment)
    assert len(calls) == 1


def test_input_publication_timeout_is_not_retried(project):
    build_workflows(project.root, project.output)
    calls = []

    def execute(argv, **kwargs):
        calls.append(argv)
        raise subprocess.TimeoutExpired(argv, 300)

    client = KaggleClient(project.root, project.output / "logs", execute=execute)
    deployment = project.output / "fine_tune"
    with pytest.raises(subprocess.TimeoutExpired):
        client.publish_inputs(deployment)
    with pytest.raises(RuntimeError, match="outcome unknown"):
        client.publish_inputs(deployment)
    assert len(calls) == 1


def test_cache_acquisition_reuses_shared_byte_verification(tmp_path, monkeypatch):
    model = {"repo_id": "test/model", "revision": "a" * 40}
    encoder = {"repo_id": "test/encoder", "revision": "b" * 40}
    payload = b"test model bytes"
    evidence = {
        "algorithm": "sha256",
        "bytes": len(payload),
        "digest": hashlib.sha256(payload).hexdigest(),
    }
    pins = tmp_path / "pins.json"
    cfg.write_json(
        pins,
        {
            "models": {
                "model": {**model, "files": {"weights.bin": evidence}},
                "encoder": {**encoder, "files": {"weights.bin": evidence}},
            }
        },
    )
    monkeypatch.setattr(cfg, "load", lambda: {"models": {"generator": model}})
    calls = []

    def download(**kwargs):
        calls.append(kwargs)
        snapshot = (
            kwargs["cache_dir"]
            / ("models--" + kwargs["repo_id"].replace("/", "--"))
            / "snapshots"
            / kwargs["revision"]
        )
        snapshot.mkdir(parents=True)
        (snapshot / kwargs["filename"]).write_bytes(payload)

    result = fetch_cache(tmp_path / "cache", pins, token="test-secret", download=download)
    assert set(result) == {"model", "encoder"}
    tokens = {call["repo_id"]: call["token"] for call in calls}
    assert tokens == {"test/model": "test-secret", "test/encoder": False}
    assert "test-secret" not in (tmp_path / "model-cache-verification.json").read_text()

    def bad_download(**kwargs):
        raise RuntimeError("network failed with test-secret")

    with pytest.raises(RuntimeError, match="Cache acquisition failed") as exc:
        fetch_cache(tmp_path / "other", pins, token="test-secret", download=bad_download)
    assert "test-secret" not in str(exc.value)


def test_missing_staged_input_and_question_changes_require_rebuild(project):
    build_workflows(project.root, project.output)
    deployment = project.output / "fine_tune"
    record = json.loads((deployment / "deployment.json").read_text())
    (deployment / "inputs" / record["input_file"]).unlink()
    cfg.write_jsonl(project.root / "data/dev_eval.jsonl", [{"id": "q1", "question": "Changed"}])
    state = local_status(project.root, deployment, "fine_tune")
    assert state["status"] == "needs_build"
    assert {"staged_inputs", "data/dev_eval.jsonl"} <= set(state["changed"])


def test_push_requires_published_inputs_without_creating_a_submission(project):
    build_workflows(project.root, project.output)
    calls = []

    def execute(argv, **kwargs):
        calls.append(argv)
        assert argv[:3] == ["kaggle", "datasets", "files"]
        return SimpleNamespace(returncode=0, stdout='{"datasetFiles": []}', stderr="")

    directory = project.output / "logs"
    client = KaggleClient(project.root, directory, execute=execute)
    with pytest.raises(ValueError, match="Publish the matching workflow inputs"):
        client.push(project.output / "fine_tune")
    assert len(calls) == 1
    assert not (directory / "submission.json").exists()
