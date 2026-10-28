"""T10 runs fully offline with small fixtures and injected GPU backends."""

import copy
import json
import random
import sys
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace

import pytest

from eth_nl2sql import cli
from eth_nl2sql import config as cfg
from eth_nl2sql import train_qlora as training
from eth_nl2sql.experiments import (
    SEEDS,
    generation_provenance,
    prediction_manifest,
    run_directory,
    tree_digest,
    write_manifest,
)
from eth_nl2sql.generation import backend as generation
from eth_nl2sql.generation.prompt import messages_digest
from eth_nl2sql.generation.runs import CONFIGS, RunConfig, prompt_rows, training_rows
from eth_nl2sql.linking.context import Linking
from eth_nl2sql.report import aggregate_seed_evaluations, write_report

CASES = json.loads((Path(__file__).parent / "fixtures/t10/cases.json").read_text())
CATALOG = json.loads(cfg.CATALOG_PATH.read_text())
LINKINGS = {case["id"]: Linking((), (), ()) for case in CASES}


class Tokenizer:
    eos_token_id = 2
    unk_token_id = 0
    model_max_length = 10000
    pad_token = None
    eos_token = "EOS"
    pad_token_id = 2

    def convert_tokens_to_ids(self, token):
        return 3

    def apply_chat_template(self, messages, **kwargs):
        # Stable, explicit tokenization with no optional package/download.
        return [7] + [ord(char) + 10 for m in messages for char in m["content"]] + [8]

    def __call__(self, text, **kwargs):
        assert kwargs == {"add_special_tokens": False}
        return {"input_ids": [ord(char) + 10 for char in text]}


class Monitor:
    def summary(self):
        return {
            "runtime_s": 1.25,
            "peak_gpu_memory_gib": 2.5,
            "hardware": {"gpus": ["fixture GPU"]},
        }


class FakeTrainingBackend:
    def __init__(self):
        self.events = []
        self.fits = []

    def seed(self, seed):
        self.events.append(("seed", seed))
        self.current_seed = seed
        random.seed(seed)

    def monitor(self):
        return Monitor()

    def tokenizer(self, config):
        self.events.append(("tokenizer", self.current_seed))
        return Tokenizer()

    def fit(self, train_rows, dev_rows, tokenizer, out_dir, config, seed, resume, provenance):
        self.events.append(("model_adapter_loader", self.current_seed))
        assert seed == self.current_seed
        assert len(train_rows) > 0 and len(dev_rows) > 0
        self.fits.append(
            (
                out_dir,
                seed,
                resume,
                copy.deepcopy(config["qlora"]),
                copy.deepcopy(train_rows),
                copy.deepcopy(dev_rows),
            )
        )
        checkpoint = out_dir / "checkpoints/checkpoint-1"
        cfg.write_json(checkpoint / "trainer_state.json", {"seed": seed})
        write_manifest(
            checkpoint / "checkpoint-manifest.json",
            provenance,
            checkpoint_sha256=tree_digest(checkpoint),
        )
        cfg.write_json(out_dir / "adapter/adapter_config.json", {"r": config["qlora"]["r"]})
        # Adapter initializations really differ with training seed in this simulation.
        cfg.write_json(out_dir / "adapter/adapter_model.safetensors", {"weight": random.random()})
        return {
            "steps": 1,
            "best_eval_loss": 0.5,
            "train_runtime_s": 1.0,
            "best_checkpoint": "checkpoints/checkpoint-1",
            "log_history": [],
        }


class FakeGenerationBackend:
    def __init__(self, fail_after=None):
        self.events = []
        self.generated = []
        self.fail_after = fail_after

    def seed(self, seed):
        self.events.append(("seed", seed))

    def monitor(self):
        return Monitor()

    def tokenizer(self, config):
        self.events.append(("tokenizer", None))
        return Tokenizer()

    def load(self, config, adapter, tokenizer):
        self.events.append(("load", adapter))
        return object()

    def generate(self, model, tokenizer, row, config):
        if self.fail_after is not None and len(self.generated) >= self.fail_after:
            raise RuntimeError("simulated session interruption")
        self.generated.append(row["id"])
        return {
            "raw_output": CASES[0]["sql"],
            "input_tokens": 10,
            "output_tokens": 5,
            "latency_ms": 2.0,
            "finish_reason": "stop",
        }


@pytest.fixture()
def experiment(tmp_path, monkeypatch):
    settings = cfg.load()
    settings["qlora"]["max_length"] = 10000
    settings["evaluation"]["bootstrap_samples"] = 20
    runs = tmp_path / "runs"
    monkeypatch.setattr(cli, "RUNS_DIR", runs)
    monkeypatch.setattr(cfg, "load", lambda: copy.deepcopy(settings))
    train = [{**CASES[0], "id": "train-1"}]
    dev = [{**CASES[1], "id": "dev-1"}]
    splits = {"train": train, "dev": dev, "dev_eval": CASES}
    for name, rows in splits.items():
        path = tmp_path / f"{name}.jsonl"
        cfg.write_jsonl(path, rows)
        monkeypatch.setitem(cli.SPLITS, name, path)
    original_read = cli._read_split
    monkeypatch.setattr(
        cli,
        "_read_split",
        lambda name, *args: original_read(name, *args) if name == "test" else splits[name],
    )
    for name in ("b3", "b3l", "b3-base", "b3l-base"):
        links = LINKINGS if CONFIGS[name].linking else None
        cfg.write_jsonl(
            runs / name / "prompts-dev_eval.jsonl",
            prompt_rows(CONFIGS[name], CASES, catalog=CATALOG, linkings=links),
        )
        if CONFIGS[name].fine_tuned:
            for split in ("train", "dev"):
                rows = training_rows(
                    CONFIGS[name],
                    splits[split],
                    catalog=CATALOG,
                    linkings={c["id"]: Linking((), (), ()) for c in splits[split]},
                )
                cfg.write_jsonl(runs / name / f"sft-{split}.jsonl", rows)
    return runs, settings


def run_training(runs, settings, backend, name="b3", seed=42, resume=False):
    inputs = runs / name
    return training.train(
        inputs / "sft-train.jsonl",
        inputs / "sft-dev.jsonl",
        run_directory(runs, name, seed),
        settings,
        name=name,
        seed=seed,
        backend=backend,
        resume=resume,
    )


def run_generation(runs, settings, backend, name="b3-base", seed=42, **kwargs):
    directory = run_directory(runs, name, seed)
    return generation.generate_file(
        runs / name / "prompts-dev_eval.jsonl",
        directory / "predictions-dev_eval.jsonl",
        settings,
        name=name,
        seed=seed,
        backend=backend,
        adapter=directory / "adapter" if CONFIGS[name].fine_tuned else None,
        **kwargs,
    )


@pytest.mark.parametrize("base,tuned", [("b3-base", "b3"), ("b3l-base", "b3l")])
def test_compact_control_matches_inference_and_training_exactly(base, tuned):
    kwargs = {"catalog": CATALOG, "linkings": LINKINGS}
    controls = prompt_rows(CONFIGS[base], CASES, **kwargs)
    prompts = prompt_rows(CONFIGS[tuned], CASES, **kwargs)
    sft = training_rows(CONFIGS[tuned], CASES, **kwargs)
    for control, prompt, target in zip(controls, prompts, sft, strict=True):
        assert control["messages"] == prompt["messages"] == target["messages"]
        assert control["prompt_sha256"] == prompt["prompt_sha256"]
    assert not CONFIGS[base].fine_tuned and CONFIGS[tuned].fine_tuned
    assert CONFIGS[base].prompt_style == CONFIGS[tuned].prompt_style == "compact"
    # Prompt choice also works independently for a custom tuned config.
    catalog_tuned = RunConfig("custom", False, False, True, prompt_style="catalog")
    assert (
        prompt_rows(catalog_tuned, CASES, catalog=CATALOG)[0]["messages"]
        == (training_rows(catalog_tuned, CASES, catalog=CATALOG)[0]["messages"])
    )


def test_six_training_runs_are_isolated_and_reproducible(experiment, monkeypatch):
    runs, settings = experiment
    backend = FakeTrainingBackend()
    monkeypatch.setattr(training, "HuggingFaceTrainingBackend", lambda: backend)
    cli.main(["train", "--config", "all", "--seed", "all"])
    assert len(backend.fits) == 6
    paths = {record[0] for record in backend.fits}
    assert paths == {run_directory(runs, name, seed) for name in ("b3", "b3l") for seed in SEEDS}
    for index, (_, seed, _, hyper, train_rows, dev_rows) in enumerate(backend.fits):
        assert backend.events[index * 3 : index * 3 + 3] == [
            ("seed", seed),
            ("tokenizer", seed),
            ("model_adapter_loader", seed),
        ]
        assert hyper == settings["qlora"]
        assert train_rows == backend.fits[index - index % 3][4]
        assert dev_rows == backend.fits[index - index % 3][5]
    before = {p: p.read_bytes() for directory in paths for p in directory.rglob("*") if p.is_file()}
    cli.main(["train", "--config", "all", "--seed", "all", "--resume"])
    assert len(backend.fits) == 6  # completed runs do not load a model again
    assert all(p.read_bytes() == content for p, content in before.items())
    weights = [tree_digest(run_directory(runs, "b3", seed) / "adapter") for seed in SEEDS]
    assert len(set(weights)) == 3
    replica = FakeTrainingBackend()
    replica.seed(43)
    assert json.loads((runs / "b3/seed-43/adapter/adapter_model.safetensors").read_text()) == {
        "weight": random.random()
    }


def test_resume_matrix_starts_missing_seeds_and_refuses_unverified_artifacts(
    experiment, monkeypatch
):
    runs, settings = experiment
    backend = FakeTrainingBackend()
    run_training(runs, settings, backend)
    monkeypatch.setattr(training, "HuggingFaceTrainingBackend", lambda: backend)
    cli.main(["train", "--config", "all", "--seed", "all", "--resume"])
    assert len(backend.fits) == 6
    orphan = runs / "orphan"
    cfg.write_json(orphan / "adapter/adapter_config.json", {})
    with pytest.raises(ValueError, match="Unverified training"):
        training.train(
            runs / "b3/sft-train.jsonl",
            runs / "b3/sft-dev.jsonl",
            orphan,
            settings,
            resume=True,
            backend=backend,
        )


@pytest.mark.parametrize("change", ["prompt", "model", "adapter", "hyperparameters"])
def test_training_resume_rejects_stale_provenance_even_if_complete(experiment, change):
    runs, settings = experiment
    backend = FakeTrainingBackend()
    run_training(runs, settings, backend)
    if change == "prompt":
        path = runs / "b3/sft-train.jsonl"
        rows = cfg.read_jsonl(path)
        rows[0]["messages"][1]["content"] += " changed"
        cfg.write_jsonl(path, rows)
    elif change == "model":
        settings["models"]["generator"]["revision"] = "0" * 40
    elif change == "hyperparameters":
        settings["qlora"]["learning_rate"] *= 2
    else:
        (runs / "b3/seed-42/adapter/adapter_model.safetensors").write_text("tampered")
    with pytest.raises(ValueError, match="[Pp]rovenance|[Aa]dapter hash"):
        run_training(runs, settings, backend, resume=True)
    assert len(backend.fits) == 1


def test_resume_verifies_checkpoint_contents_and_training_identity(experiment):
    runs, settings = experiment
    backend = FakeTrainingBackend()
    run_training(runs, settings, backend)
    directory = runs / "b3/seed-42"
    manifest_path = directory / "training-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["status"] = "running"
    cfg.write_json(manifest_path, manifest)
    run_training(runs, settings, backend, resume=True)
    assert backend.fits[-1][2] == directory / "checkpoints/checkpoint-1"
    manifest["status"] = "running"
    cfg.write_json(manifest_path, manifest)
    state = directory / "checkpoints/checkpoint-1/trainer_state.json"
    state.write_text("tampered")
    with pytest.raises(ValueError, match="Checkpoint hash"):
        run_training(runs, settings, backend, resume=True)


def test_sql_is_whole_or_dropped_and_empty_retained_splits_fail(experiment):
    runs, settings = experiment
    path = runs / "b3/sft-train.jsonl"
    rows = cfg.read_jsonl(path)
    full = training.encode_row(Tokenizer(), rows[0], 10000)
    target = Tokenizer()(rows[0]["target"], add_special_tokens=False)["input_ids"] + [3]
    assert [t for t in full["labels"] if t != -100] == target
    long = copy.deepcopy(rows[0])
    long["id"] = "long-sql"
    long["target"] *= 100
    cfg.write_jsonl(path, [*rows, long])
    backend = FakeTrainingBackend()
    summary = run_training(runs, settings, backend)
    stats = summary["preflight"]["train"]
    assert stats["input_rows"] == 2 and stats["kept_rows"] == 1
    assert stats["dropped_over_max_length"] == 1
    assert stats["dropped"][0]["id"] == "long-sql"
    assert stats["total_tokens"] == stats["kept_tokens"] + stats["dropped_tokens"]
    assert summary["runtime_s"] == 1.25 and summary["peak_gpu_memory_gib"] == 2.5
    settings["qlora"]["max_length"] = 1
    with pytest.raises(ValueError, match="no rows after"):
        run_training(runs, settings, backend, seed=43)
    assert len(backend.fits) == 1
    preflight = json.loads((runs / "b3/seed-43/preflight-training.json").read_text())
    assert not preflight["passed"] and preflight["train"]["kept_rows"] == 0
    assert not (runs / "b3/seed-43/adapter").exists()


@pytest.mark.parametrize("bad", ["empty", "duplicate", "missing_sql", "overlapping"])
def test_training_rejects_invalid_inputs_before_gpu_initialization(experiment, bad):
    runs, settings = experiment
    path = runs / "b3/sft-train.jsonl"
    rows = cfg.read_jsonl(path)
    if bad == "empty":
        rows = []
    elif bad == "duplicate":
        rows *= 2
    elif bad == "missing_sql":
        rows[0]["target"] = ""
    else:
        rows[0]["id"] = "dev-1"
    cfg.write_jsonl(path, rows)
    backend = FakeTrainingBackend()
    with pytest.raises(ValueError):
        run_training(runs, settings, backend)
    assert backend.events == []


@pytest.mark.parametrize("change", ["prompt", "model", "generation", "predictions"])
def test_generation_checks_resume_provenance_before_loading_model(experiment, change):
    runs, settings = experiment
    backend = FakeGenerationBackend()
    assert run_generation(runs, settings, backend) == 2
    assert run_generation(runs, settings, backend) == 0
    assert backend.events[0] == ("seed", settings["generation"]["seed"])
    loads = len(backend.events)
    if change == "prompt":
        path = runs / "b3-base/prompts-dev_eval.jsonl"
        rows = cfg.read_jsonl(path)
        rows[0]["messages"][1]["content"] += " changed"
        rows[0]["prompt_sha256"] = messages_digest(rows[0]["messages"])
        cfg.write_jsonl(path, rows)
    elif change == "model":
        settings["models"]["generator"]["revision"] = "0" * 40
    elif change == "generation":
        settings["generation"]["max_new_tokens"] += 1
    else:
        path = runs / "b3-base/seed-42/predictions-dev_eval.jsonl"
        rows = cfg.read_jsonl(path)
        rows[0]["raw_output"] = "SELECT 999"
        cfg.write_jsonl(path, rows)
    with pytest.raises(ValueError, match="[Pp]rovenance|hash mismatch"):
        run_generation(runs, settings, backend)
    assert len(backend.events) == loads


def test_generation_recovers_interruption_and_limit_without_duplicate_ids(experiment):
    runs, settings = experiment
    with pytest.raises(RuntimeError, match="interruption"):
        run_generation(runs, settings, FakeGenerationBackend(fail_after=1))
    backend = FakeGenerationBackend()
    assert run_generation(runs, settings, backend) == 1
    assert backend.generated == ["q2"]
    assert run_generation(runs, settings, backend, seed=43, limit=1) == 1
    assert run_generation(runs, settings, backend, seed=43) == 1
    for seed in (42, 43):
        path = runs / f"b3-base/seed-{seed}/predictions-dev_eval.jsonl"
        assert [r["id"] for r in cfg.read_jsonl(path)] == ["q1", "q2"]
        manifest = json.loads(prediction_manifest(path).read_text())
        assert manifest["status"] == "complete"
        assert manifest["input_tokens"] == 20 and manifest["output_tokens"] == 10
        assert manifest["sessions"][-1]["peak_gpu_memory_gib"] == 2.5


def test_resume_after_last_append_finalizes_without_model_loading(experiment):
    runs, settings = experiment
    run_generation(runs, settings, FakeGenerationBackend())
    path = runs / "b3-base/seed-42/predictions-dev_eval.jsonl"
    manifest_path = prediction_manifest(path)
    manifest = json.loads(manifest_path.read_text())
    manifest["status"] = "running"
    manifest.pop("predictions_sha256")
    cfg.write_json(manifest_path, manifest)
    backend = FakeGenerationBackend()
    assert run_generation(runs, settings, backend) == 0
    assert backend.events == []
    recovered = json.loads(manifest_path.read_text())
    assert recovered["status"] == "complete" and recovered["generated_rows"] == 2
    assert recovered["recovered_after_interruption"]
    assert not recovered["resource_measurements_complete"]
    # A running manifest has no file checksum yet, but individual records stay protected.
    manifest["status"] = "running"
    cfg.write_json(manifest_path, manifest)
    rows = cfg.read_jsonl(path)
    rows[0]["raw_output"] = "SELECT 999"
    cfg.write_jsonl(path, rows)
    with pytest.raises(ValueError, match="Prediction provenance/hash mismatch"):
        run_generation(runs, settings, backend)


@pytest.mark.parametrize("revision", ["main", "v1", "", "a" * 39])
def test_model_requires_immutable_pin_before_gpu_initialization(experiment, revision):
    runs, settings = experiment
    settings["models"]["generator"]["revision"] = revision
    backend = FakeGenerationBackend()
    with pytest.raises(ValueError, match="revision"):
        run_generation(runs, settings, backend)
    assert backend.events == []


def test_unmanifested_predictions_and_wrong_adapters_are_rejected(experiment):
    runs, settings = experiment
    path = runs / "b3-base/seed-42/predictions-dev_eval.jsonl"
    cfg.write_jsonl(path, [{"id": "q1"}])
    with pytest.raises(ValueError, match="Missing provenance"):
        run_generation(runs, settings, FakeGenerationBackend())
    with pytest.raises(ValueError, match="must not load an adapter"):
        generation_provenance(
            runs / "b3-base/prompts-dev_eval.jsonl", settings, "b3-base", 42, path
        )
    run_training(runs, settings, FakeTrainingBackend())
    adapter = runs / "b3/seed-42/adapter"
    with pytest.raises(ValueError, match="Provenance mismatch"):
        generation_provenance(runs / "b3l/prompts-dev_eval.jsonl", settings, "b3l", 42, adapter)
    with pytest.raises(ValueError, match="Provenance mismatch"):
        generation_provenance(runs / "b3/prompts-dev_eval.jsonl", settings, "b3", 43, adapter)
    run_generation(runs, settings, FakeGenerationBackend(), name="b3")
    (adapter / "adapter_model.safetensors").write_text("changed")
    with pytest.raises(ValueError, match="adapter hash"):
        run_generation(runs, settings, FakeGenerationBackend(), name="b3")


def test_preflight_does_not_load_model_or_truncate_prompts(experiment, monkeypatch):
    runs, _ = experiment
    backend = FakeGenerationBackend()
    monkeypatch.setattr(generation, "HuggingFaceGenerationBackend", lambda: backend)
    cli.main(["preflight", "--config", "b3-base"])
    cli.main(["preflight", "--config", "b3", "--training", "--seed", "all"])
    assert all(event[0] != "load" for event in backend.events)
    tokenizer = Tokenizer()
    tokenizer.model_max_length = 2
    backend.tokenizer = lambda config: tokenizer
    with pytest.raises(SystemExit, match="exceed"):
        cli.main(["generate", "--config", "b3-base"])
    report = json.loads((runs / "b3-base/seed-42/preflight-predictions-dev_eval.json").read_text())
    assert not report["passed"] and not report["truncation"]
    assert report["dropped_rows"] == 0
    assert not (runs / "b3-base/seed-42/predictions-dev_eval.jsonl").exists()


def test_draft_test_gate_covers_new_commands_before_tokenizer(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("Draft test must be gated before model/tokenizer loading")

    monkeypatch.setattr(generation, "load_tokenizer", forbidden)
    for args in (
        ["preflight", "--config", "b3-base"],
        ["preflight", "--config", "b3", "--training"],
        ["prompts", "--config", "b3", "--training"],
        ["generate", "--config", "b3l", "--seed", "all"],
        ["evaluate", "--config", "b3l", "--seed", "all"],
        ["report"],
    ):
        with pytest.raises(SystemExit, match="Final test v2 is not frozen"):
            cli.main([*args, "--split", "test"])


def test_end_to_end_six_runs_evaluation_and_seed_report(experiment, monkeypatch, store, tmp_path):
    runs, settings = experiment
    train_backend = FakeTrainingBackend()
    generate_backend = FakeGenerationBackend()
    monkeypatch.setattr(training, "HuggingFaceTrainingBackend", lambda: train_backend)
    monkeypatch.setattr(generation, "HuggingFaceGenerationBackend", lambda: generate_backend)
    from eth_nl2sql.store import build

    monkeypatch.setattr(build, "connect", lambda path: nullcontext(store))
    cli.main(["train", "--config", "all", "--seed", "all"])
    for name in ("b3", "b3l"):
        cli.main(["generate", "--config", name, "--seed", "all"])
        cli.main(["evaluate", "--config", name, "--seed", "all"])
    for name in ("b3-base", "b3l-base"):
        cli.main(["generate", "--config", name])
        cli.main(["evaluate", "--config", name])
    report = write_report(runs, "dev_eval", tmp_path / "RESULTS.md")
    data = json.loads((runs / "seed-summary-dev_eval.json").read_text())
    assert data["b3"]["n_questions"] == 2  # never six independent observations
    assert data["b3"]["n_seeds"] == 3 and data["b3"]["complete"]
    assert data["b3"]["metrics"]["execution_accuracy"] == {"mean": 1.0, "std": 0.0}
    assert all(f"b3/seed-{seed}" in report.read_text() for seed in SEEDS)
    assert "b3-base/seed-42" in report.read_text()
    assert "predictions are never pooled" in report.read_text()
    # Every seed has its own predictions, evaluated cases, summaries and manifests.
    assert len(list((runs / "b3").glob("seed-*/eval-dev_eval.manifest.json"))) == 3
    assert len(list((runs / "b3l").glob("seed-*/predictions-dev_eval.manifest.json"))) == 3
    # A changed prediction cannot silently be reevaluated or included in a fresh report.
    path = runs / "b3/seed-42/predictions-dev_eval.jsonl"
    path.write_text(path.read_text().replace("SELECT", "SELEKT"))
    with pytest.raises(SystemExit, match="hash mismatch"):
        cli.main(["evaluate", "--config", "b3"])
    with pytest.raises(ValueError, match="stale predictions"):
        write_report(runs, "dev_eval", tmp_path / "RESULTS.md")


def test_seed_statistics_and_mismatched_protocol_rejection():
    def evaluation(seed, value):
        return {
            "config": "b3",
            "seed": seed,
            "split": "dev_eval",
            "n": 100,
            "dataset_sha256": "data",
            "case_ids_sha256": "ids",
            "store": {"scope": "sample"},
            "model_sha256": "model",
            "prompts_sha256": "prompt",
            "generation_sha256": "gen",
            "evaluation_settings_sha256": "eval",
            "training_protocol_sha256": "training",
            "by_group": {"subset:entity": {"n": 50, "execution_accuracy": value}},
            **{
                metric: value
                for metric in (
                    "execution_accuracy",
                    "valid_sql_rate",
                    "format_ok_rate",
                    "exact_match",
                    "structural_match",
                    "answer_f1",
                )
            },
        }

    evaluations = {
        seed: evaluation(seed, value) for seed, value in zip(SEEDS, (0.4, 0.5, 0.6), strict=True)
    }
    report = aggregate_seed_evaluations(evaluations)
    assert report["n_questions"] == 100 and report["n_seeds"] == 3
    assert report["metrics"]["execution_accuracy"]["mean"] == pytest.approx(0.5)
    assert report["metrics"]["execution_accuracy"]["std"] == pytest.approx(0.1)
    partial = aggregate_seed_evaluations({42: evaluations[42]})
    assert partial["missing_seeds"] == [43, 44] and not partial["complete"]
    assert partial["metrics"]["execution_accuracy"]["std"] is None
    for key in (
        "dataset_sha256",
        "case_ids_sha256",
        "model_sha256",
        "prompts_sha256",
        "generation_sha256",
        "training_protocol_sha256",
        "n",
        "store",
    ):
        changed = copy.deepcopy(evaluations)
        changed[44][key] = "mismatch"
        with pytest.raises(ValueError, match="Cannot aggregate"):
            aggregate_seed_evaluations(changed)


def test_real_training_setup_seeds_adapter_and_loader_and_keeps_dev_selection(
    experiment,
    monkeypatch,
):
    """Exercise the production HF wiring using package doubles, without torch/GPU."""
    runs, settings = experiment
    events = []
    arguments = []

    class Model:
        config = SimpleNamespace(use_cache=True)

        def save_pretrained(self, directory):
            cfg.write_json(Path(directory) / "adapter_config.json", {"seed": random.random()})

    class Trainer:
        def __init__(self, **kwargs):
            events.append("loader")
            args = kwargs["args"]
            assert args.seed == args.data_seed == 44
            self.state = SimpleNamespace(
                best_metric=0.5,
                log_history=[],
                best_model_checkpoint=str(Path(args.output_dir) / "checkpoint-1"),
            )

        def train(self, **kwargs):
            return SimpleNamespace(global_step=1, metrics={"train_runtime": 1.0})

    class Arguments(SimpleNamespace):
        def __init__(self, **kwargs):
            arguments.append(kwargs)
            super().__init__(**kwargs)

    tokenizer = Tokenizer()
    tokenizer.save_pretrained = lambda path: None
    model = Model()

    def seed(value):
        events.append("seed")
        random.seed(value)

    def load(*args, **kwargs):
        events.append("model")
        assert events[0] == "seed"
        return model, tokenizer

    def adapter(model, config):
        events.append("adapter")
        return model

    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            set_seed=seed,
            TrainingArguments=Arguments,
            Trainer=Trainer,
            TrainerCallback=object,
            EarlyStoppingCallback=lambda **kwargs: None,
        ),
    )
    monkeypatch.setitem(
        sys.modules,
        "peft",
        SimpleNamespace(
            LoraConfig=lambda **kwargs: kwargs,
            get_peft_model=adapter,
            prepare_model_for_kbit_training=lambda model, **kwargs: model,
        ),
    )
    monkeypatch.setattr(training, "load_generator", load)
    backend = training.HuggingFaceTrainingBackend()
    backend.seed(44)
    backend.fit([{}], [{}], tokenizer, runs / "hf-fixture", settings, 44, None, {})
    assert events == ["seed", "model", "adapter", "loader"]
    args = arguments[0]
    assert args["load_best_model_at_end"] and args["metric_for_best_model"] == "eval_loss"
    assert args["greater_is_better"] is False and args["eval_steps"] == args["save_steps"]
    assert args["learning_rate"] == settings["qlora"]["learning_rate"]
