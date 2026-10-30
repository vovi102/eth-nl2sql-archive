"""Kaggle lifecycle contracts, exercised without network or GPU access."""

import hashlib
import importlib
import json
import subprocess
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from eth_nl2sql import config as cfg
from eth_nl2sql.generation.runs import CONFIGS, Job
from eth_nl2sql.gpu_notebook import NotebookSpec, build_notebook
from eth_nl2sql.gpu_workflow import collect_outputs
from eth_nl2sql.kaggle import KaggleClient, KaggleSettings, load_settings


def response(stdout="", *, returncode=0, stderr=""):
    return SimpleNamespace(stdout=stdout, stderr=stderr, returncode=returncode)


def notebook(path, kernel="tester/inference"):
    cfg.write_json(path / "kernel-metadata.json", {"id": kernel, "code_file": "run.py"})
    (path / "run.py").write_text("print('run')\n")
    return path


def test_only_adapter_producers_get_dedicated_names():
    settings = KaggleSettings(
        "tester", "cache", training_kernels={"b3-seed-42": "published-original-adapter"}
    )
    assert settings.kernel() == settings.kernel("pilot") == "tester/eth-nl2sql-inference"
    assert settings.kernel(Job(CONFIGS["b3-base"], 42)) == settings.kernel()
    assert settings.kernel("b3-seed-42") == "tester/published-original-adapter"
    assert settings.kernel("b3l-seed-42") == "tester/eth-nl2sql-b3l-seed-42"
    assert settings.kernel("b3-seed-43") == "tester/eth-nl2sql-b3-seed-43"


def test_existing_adapter_identity_is_explicit_in_configuration():
    settings = load_settings()
    assert settings.kernel("b3-seed-42") != settings.kernel()
    assert "b3-seed-42" in settings.training_kernels
    assert not hasattr(settings, "run_tag")


def test_diagnostic_builder_is_repeatable_and_mounts_the_planned_adapter(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(cfg.ROOT / "scripts"))
    builder = importlib.import_module("t11b_diagnose_notebook")
    original = importlib.import_module("t11a_notebook").SPEC
    archive = tmp_path / "inputs.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr(
            "reports/experiments/diagnosis/plan.json",
            json.dumps({"adapter_kernel": "producer/frozen-adapter"}),
        )
    output = tmp_path / "notebook"
    snapshots = []
    for _ in range(2):
        builder.build(archive, output, "tester/inference", cache_kernel="tester/cache")
        snapshots.append(
            {
                p.relative_to(output).as_posix(): p.read_bytes()
                for p in output.rglob("*")
                if p.is_file()
            }
        )
    assert snapshots[0] == snapshots[1]
    assert importlib.import_module("t11a_notebook").SPEC == original
    metadata = json.loads((output / "kernel-metadata.json").read_text())
    assert metadata["kernel_sources"] == ["tester/cache", "producer/frozen-adapter"]
    assert metadata["code_file"] == "t11b-diagnosis.ipynb"
    built = json.loads((output / metadata["code_file"]).read_text())
    source = "\n".join(c["source"] for c in built["cells"] if c["cell_type"] == "code")
    assert "PAYLOAD" not in source
    assert "scripts/t11b_diagnose.py" in source
    assert "configs/t11b-gpu-requirements.txt" in source
    assert "for line in process.stdout" in source
    compile(source, metadata["code_file"], "exec")
    with pytest.raises(ValueError, match="overwrite one of its source"):
        builder.build(archive, tmp_path / "overwrite", "producer/frozen-adapter")
    assert not (tmp_path / "overwrite").exists()


def test_large_inputs_do_not_enlarge_notebook_source(tmp_path):
    archive = tmp_path / "inputs.zip"
    spec = NotebookSpec("diagnostic", "run.py", "requirements.txt")
    import random

    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("data.bin", random.Random(42).randbytes(800_000))
    output = tmp_path / "out"
    build_notebook(archive, output, "tester/inference", spec)
    assert (output / "diagnostic.ipynb").stat().st_size < 20_000
    assert json.loads((output / "kernel-metadata.json").read_text())["dataset_sources"]


def test_push_pins_version_and_collects_only_that_version_in_a_fresh_directory(tmp_path):
    directory = tmp_path / "reports/job"
    calls, sleeps, received = [], [], []
    statuses = iter(("RUNNING", "COMPLETE"))
    payload = b'{"id":"q1"}\n'
    manifest = {"predictions.jsonl": hashlib.sha256(payload).hexdigest()}

    def execute(argv, **kwargs):
        calls.append(argv)
        if argv[:3] == ["kaggle", "kernels", "push"]:
            return response("Kernel version 7 successfully pushed. Please check progress at URL")
        assert argv[3] == "tester/inference/7"
        if argv[2] == "status":
            return response(
                f"tester/inference/7 has status KernelWorkerStatus.{next(statuses)}\n"
                'Failure message: "Previous version COMPLETE"'
            )
        assert argv[2] == "output"
        target = Path(argv[argv.index("-p") + 1]) / "output.zip"
        assert not target.exists()
        with zipfile.ZipFile(target, "w") as bundle:
            bundle.writestr("predictions.jsonl", payload)
            bundle.writestr("manifest.json", json.dumps(manifest))
        return response()

    client = KaggleClient(tmp_path, directory, execute=execute, sleep=sleeps.append)
    built = notebook(tmp_path / "notebook")
    with client.session("tester/inference"):
        reference = client.push(built)
        assert client.push(built) == reference  # A saved receipt prevents a duplicate push.

        def receive(archive):
            received.append(archive)
            collect_outputs(
                tmp_path / "retained", archive, "manifest.json", can_replace=lambda _: False
            )

        assert client.collect(reference, "output.zip", receive) == "COMPLETE"
    assert sleeps == [30]
    assert len([argv for argv in calls if argv[2] == "push"]) == 1
    assert (tmp_path / "retained/predictions.jsonl").read_bytes() == payload
    assert json.loads((directory / "submission.json").read_text())["kernel_ref"] == reference
    assert all(not path.exists() for path in received)
    assert not list(tmp_path.rglob("*.zip"))


def test_push_never_retries_when_submission_outcome_is_ambiguous(tmp_path):
    calls = []

    def execute(argv, **kwargs):
        calls.append(argv)
        raise subprocess.TimeoutExpired(argv, 300)

    client = KaggleClient(tmp_path, tmp_path / "job", execute=execute)
    built = notebook(tmp_path / "notebook")
    with pytest.raises(subprocess.TimeoutExpired):
        client.push(built)
    with pytest.raises(RuntimeError, match="outcome unknown"):
        client.push(built)
    assert len(calls) == 1


def test_existing_producer_output_cannot_be_pushed_again(tmp_path):
    calls = []

    def execute(argv, **kwargs):
        calls.append(argv)
        return response(json.dumps([{"ref": "tester/adapter"}]))

    client = KaggleClient(tmp_path, tmp_path / "job", execute=execute)
    with pytest.raises(ValueError, match="preserve its output"):
        client.push(notebook(tmp_path / "notebook", "tester/adapter"), producer=True)
    assert [argv[2] for argv in calls] == ["list"]
    assert not (tmp_path / "job/submission.json").exists()


def test_shared_kernel_requires_a_version_before_any_remote_command(tmp_path):
    client = KaggleClient(tmp_path, tmp_path / "job", execute=lambda *_a, **_k: pytest.fail())
    with pytest.raises(ValueError, match="submitted version"):
        client.collect("tester/inference", "output.zip", lambda _: pytest.fail())


def test_kernel_lock_is_shared_across_controllers_and_versions(tmp_path):
    first = KaggleClient(tmp_path, tmp_path / "train")
    second = KaggleClient(tmp_path, tmp_path / "diagnosis")
    with first.session("tester/inference/1"):
        with pytest.raises(RuntimeError, match="Another controller"):
            with second.session("tester/inference/2"):
                pytest.fail("Concurrent controller acquired the kernel")
    with second.session("tester/inference/2"):
        pass


@pytest.mark.parametrize("invalid", ["plan", "checksum", "traversal"])
def test_collect_checks_plan_and_all_hashes_before_writing(tmp_path, invalid):
    archive = tmp_path / "output.zip"
    destination = tmp_path / "collected"
    expected = {"adapter_kernel": "tester/adapter"}
    plan = {"adapter_kernel": "other/adapter"} if invalid == "plan" else expected
    members = {"plan.json": json.dumps(plan).encode(), "predictions.jsonl": b"prediction"}
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in members.items()}
    if invalid == "checksum":
        manifest["predictions.jsonl"] = "0" * 64
    if invalid == "traversal":
        manifest["../escape"] = hashlib.sha256(b"escape").hexdigest()
        members["../escape"] = b"escape"
    with zipfile.ZipFile(archive, "w") as bundle:
        for name, data in members.items():
            bundle.writestr(name, data)
        bundle.writestr("manifest.json", json.dumps(manifest))
    with pytest.raises(ValueError):
        collect_outputs(
            destination,
            archive,
            "manifest.json",
            can_replace=lambda _: False,
            expected_json={"plan.json": expected},
        )
    assert not destination.exists()
    assert not (tmp_path / "escape").exists()


def test_training_controller_respects_current_hold_without_remote_calls(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(cfg.ROOT / "scripts"))
    controller = importlib.import_module("t11b_continue")
    monkeypatch.setattr(controller, "ROOT", tmp_path)
    monkeypatch.setattr(controller, "REPORT", tmp_path / "reports/experiments")
    cfg.write_json(
        controller.REPORT / "diagnosis/scaling-decision.json",
        {"decision": "hold_for_further_development"},
    )
    monkeypatch.setattr(
        controller, "KaggleClient", lambda *_: pytest.fail("Remote work during hold")
    )
    controller.continue_jobs(KaggleSettings("tester", "cache"))
    assert not (controller.REPORT / "continuation.json").exists()


def test_training_controller_saves_the_submitted_version_and_does_not_resubmit(
    tmp_path, monkeypatch
):
    from contextlib import nullcontext

    monkeypatch.syspath_prepend(str(cfg.ROOT / "scripts"))
    controller = importlib.import_module("t11b_continue")
    monkeypatch.setattr(controller, "ROOT", tmp_path)
    monkeypatch.setattr(controller, "REPORT", tmp_path / "reports/experiments")
    monkeypatch.setattr(controller, "JOBS", ("pilot",))
    for name in ("inputs-manifest.json", "bundle.json"):
        cfg.write_json(controller.REPORT / name, {})
    calls = []

    class Client:
        def __init__(self, root, directory):
            self.directory = directory

        def session(self, kernel):
            return nullcontext()

        def command(self, argv, name):
            calls.append(argv)
            return json.dumps([{"resource": "GPU", "remaining": "10h"}])

        def push(self, path, *, producer):
            assert not producer
            calls.append("push")
            return "tester/eth-nl2sql-inference/12"

        def collect(self, reference, filename, receive, **kwargs):
            assert reference == "tester/eth-nl2sql-inference/12"
            assert kwargs["require_version"]
            calls.append("collect")
            return "COMPLETE"

    def evaluate(job):
        cfg.write_json(
            controller.REPORT / job / "eval.json",
            {"n": 10, "valid_sql_rate": 0, "execution_accuracy": 0, "scope": "pilot"},
        )

    monkeypatch.setattr(controller, "KaggleClient", Client)
    monkeypatch.setattr(controller, "evaluate", evaluate)
    settings = KaggleSettings("tester", "cache")
    controller.continue_jobs(settings)
    state = json.loads((controller.REPORT / "continuation.json").read_text())
    assert state["status"] == "complete"
    assert state["jobs"]["pilot"]["kernel_ref"] == "tester/eth-nl2sql-inference/12"
    previous = list(calls)
    controller.continue_jobs(settings)
    assert calls == previous


def test_new_producer_is_created_only_after_a_successful_absence_check(tmp_path):
    calls = []

    def execute(argv, **kwargs):
        calls.append(argv[2])
        if argv[2] == "list":
            return response("Not found\n")
        return response("Kernel version 1 successfully pushed. Please check progress at URL")

    client = KaggleClient(tmp_path, tmp_path / "job", execute=execute)
    assert client.push(notebook(tmp_path / "notebook", "tester/new-adapter"), producer=True) == (
        "tester/new-adapter/1"
    )
    assert calls == ["list", "push"]
