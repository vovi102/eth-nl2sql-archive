"""Kaggle identities and the shared submit/observe/collect lifecycle."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
import tomllib
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from eth_nl2sql import config as cfg
from eth_nl2sql.artifacts import atomic_write_json, json_digest
from eth_nl2sql.generation.runs import Job


@dataclass(frozen=True)
class KaggleSettings:
    owner: str
    environment_cache: str
    inference_kernel: str = "eth-nl2sql-inference"
    training_kernels: dict[str, str] = field(default_factory=dict)
    inputs_dataset: str = "eth-nl2sql-inputs"

    def _owned(self, slug: str) -> str:
        return slug if "/" in slug else f"{self.owner}/{slug}"

    @property
    def cache_kernel(self) -> str:
        return self._owned(self.environment_cache)

    @property
    def input_dataset(self) -> str:
        return self._owned(self.inputs_dataset)

    def kernel(self, job: str | Job | None = None) -> str:
        """Training outputs have stable identities; inference jobs share versions."""
        selected = Job.parse(job) if job is not None else None
        if selected is None or not selected.config.fine_tuned:
            return self._owned(self.inference_kernel)
        return self._owned(
            self.training_kernels.get(selected.identifier, f"eth-nl2sql-{selected.identifier}")
        )


def load_settings(path: Path | None = None) -> KaggleSettings:
    with (path or cfg.ROOT / "configs/kaggle.toml").open("rb") as handle:
        values = tomllib.load(handle)
    for key in ("owner", "environment_cache", "inference_kernel", "inputs_dataset"):
        override = os.environ.get(f"ETH_NL2SQL_KAGGLE_{key.upper()}")
        if override is not None:
            values[key] = override
    return KaggleSettings(**values)


@contextmanager
def exclusive_lock(path: Path) -> Iterator[None]:
    """Hold a controller/kernel lock through submission and verified collection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f"Another controller holds {path}") from None
        lock.seek(0)
        lock.truncate()
        lock.write(f"{os.getpid()}\n")
        lock.flush()
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


class KaggleClient:
    """Keep pinned submissions, polling, downloads and collection in one place.

    Callers hold session() while using a shared kernel, then supply a collector
    that validates the job's manifest before accepting output. Commands and time
    are injected so the same lifecycle can be exercised entirely offline.
    """

    def __init__(
        self,
        root: Path,
        directory: Path,
        *,
        execute: Callable = subprocess.run,
        sleep: Callable = time.sleep,
        monotonic: Callable = time.monotonic,
    ):
        self.root = root
        self.directory = directory
        self.execute = execute
        self.sleep = sleep
        self.monotonic = monotonic

    def session(self, kernel: str):
        identity = "/".join(kernel.split("/")[:2])
        key = hashlib.sha256(identity.encode()).hexdigest()
        return exclusive_lock(self.root / ".cache/kaggle-locks" / f"{key}.lock")

    def command(self, argv: list[str], name: str, *, attempts: int = 3) -> str:
        log = self.directory / name
        log.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(attempts):
            try:
                result = self.execute(
                    argv, cwd=self.root, capture_output=True, text=True, timeout=300
                )
            except subprocess.TimeoutExpired as exc:
                log.write_text(f"Command timed out: {argv!r}\n{exc}")
                if attempt == attempts - 1:
                    raise
            else:
                output = result.stdout + (result.stderr or "")
                log.write_text(output)
                if result.returncode == 0:
                    return output
                if attempt == attempts - 1:
                    raise RuntimeError(f"Command failed; inspect {log}")
            self.sleep(5)
        raise AssertionError("No command attempt")

    def push(self, notebook: Path, *, producer: bool = False) -> str:
        metadata = json.loads((notebook / "kernel-metadata.json").read_text())
        kernel = metadata["id"]
        identity = json_digest(
            {
                "metadata": metadata,
                "source_sha256": cfg.sha256_file(notebook / metadata["code_file"]),
            }
        )
        receipt = self.directory / "submission.json"
        if receipt.exists():
            previous = json.loads(receipt.read_text())
            if previous["identity"] != identity:
                raise ValueError("Submission inputs changed; use a new job directory")
            if previous.get("kernel_ref"):
                return previous["kernel_ref"]
            raise RuntimeError(
                "Submission outcome unknown; inspect push.log before submitting again"
            )
        if producer and self._producer_exists(kernel):
            raise ValueError(f"Producer kernel already exists; preserve its output: {kernel}")
        if (notebook / "deployment.json").exists() and not self.inputs_available(notebook):
            raise ValueError("Publish the matching workflow inputs before running this notebook")
        record = {"kernel": kernel, "identity": identity, "status": "submitting"}
        atomic_write_json(receipt, record)
        # Never retry a push: a timeout can still have created a remote version.
        argv = ["kaggle", "kernels", "push", "-p", str(notebook), "--timeout", "43200"]
        if metadata.get("enable_gpu", True):
            argv += ["--accelerator", "NvidiaTeslaT4"]
        output = self.command(
            argv,
            "push.log",
            attempts=1,
        )
        match = re.search(r"Kernel version (\d+) successfully pushed", output)
        if match is None:
            raise RuntimeError("Push did not confirm a version; inspect push.log before retrying")
        reference = f"{kernel}/{int(match[1])}"
        atomic_write_json(receipt, {**record, "status": "submitted", "kernel_ref": reference})
        return reference

    def inputs_available(self, notebook: Path) -> bool:
        deployment = json.loads((notebook / "deployment.json").read_text())
        output = self.command(
            [
                "kaggle",
                "datasets",
                "files",
                deployment["input_dataset"],
                "--format",
                "json",
                "--page-size",
                "200",
            ],
            "input-files.json",
            attempts=1,
        )
        rows = json.loads(output)
        if isinstance(rows, dict):
            rows = rows.get("datasetFiles", rows.get("dataset_files", rows.get("files", [])))
        return any(row["name"] == deployment["input_file"] for row in rows)

    def publish_inputs(self, notebook: Path, *, create: bool = False) -> dict:
        """Publish only the input dataset; never start or save a kernel version."""
        deployment = json.loads((notebook / "deployment.json").read_text())
        inputs = notebook / "inputs"
        archive = inputs / deployment["input_file"]
        checksum = deployment["provenance"]["input_sha256"]
        if cfg.sha256_file(archive) != checksum:
            raise ValueError("Staged inputs changed; rebuild before publishing")
        metadata = json.loads((inputs / "dataset-metadata.json").read_text())
        if metadata["id"] != deployment["input_dataset"]:
            raise ValueError("Input dataset identity differs from the notebook")
        receipt = self.directory / f"inputs-submission-{checksum}.json"
        if receipt.exists():
            record = json.loads(receipt.read_text())
            if record["dataset"] != metadata["id"]:
                raise ValueError("Input dataset changed; use a new deployment directory")
            if record["status"] == "submitted":
                return record
            raise RuntimeError("Input publication outcome unknown; inspect inputs-publish.log")
        record = {"dataset": metadata["id"], "sha256": checksum, "status": "submitting"}
        atomic_write_json(receipt, record)
        argv = [
            "kaggle",
            "datasets",
            "create" if create else "version",
            "-p",
            str(inputs),
            "--keep-tabular",
            "--dir-mode",
            "skip",
        ]
        if not create:
            argv += ["-m", f"Workflow inputs SHA256 {checksum}"]
        # A timeout may already have created the dataset version. Never retry blindly.
        self.command(argv, "inputs-publish.log", attempts=1)
        record["status"] = "submitted"
        atomic_write_json(receipt, record)
        return record

    def sync_status(self, notebook: Path) -> dict:
        """Compare local and remote code without executing or saving a notebook."""
        from eth_nl2sql.gpu_notebook import notebook_source

        metadata = json.loads((notebook / "kernel-metadata.json").read_text())
        local = json.loads((notebook / metadata["code_file"]).read_text())
        result = {
            "kernel": metadata["id"],
            "local_provenance": local["metadata"].get("eth_nl2sql"),
        }
        self.directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="kaggle-inspect-") as temporary:
            self.command(
                ["kaggle", "kernels", "pull", metadata["id"], "-p", temporary, "-m"],
                "pull.log",
                attempts=1,
            )
            remote_metadata = json.loads((Path(temporary) / "kernel-metadata.json").read_text())
            remote = json.loads((Path(temporary) / remote_metadata["code_file"]).read_text())
        result["remote_provenance"] = remote["metadata"].get("eth_nl2sql")
        changed = []
        if notebook_source(local) != notebook_source(remote):
            changed.append("notebook_source")
        for key in ("dataset_sources", "kernel_sources", "model_sources"):
            if sorted(metadata.get(key, [])) != sorted(remote_metadata.get(key, [])):
                changed.append(key)
        for key in ("enable_gpu", "enable_internet", "is_private"):
            actual = remote_metadata.get(key, False)
            if isinstance(actual, str):
                actual = actual.lower() == "true"
            if metadata.get(key, False) != actual:
                changed.append(key)
        try:
            available = self.inputs_available(notebook)
        except (RuntimeError, subprocess.TimeoutExpired):
            available = False
        return {
            **result,
            "status": "different" if changed else "in_sync",
            "changed": changed,
            "input_file_available": available,
        }

    def _producer_exists(self, kernel: str) -> bool:
        # A missing/private kernel can return 403 from status. List our own
        # notebooks instead of treating permission errors as proof of absence.
        owner, slug = kernel.split("/")
        page = 1
        while True:
            output = self.command(
                [
                    "kaggle",
                    "kernels",
                    "list",
                    "--mine",
                    "--user",
                    owner,
                    "--search",
                    slug,
                    "--format",
                    "json",
                    "--page-size",
                    "200",
                    "--page",
                    str(page),
                ],
                "producer-list.json",
            )
            rows_text = "\n".join(
                line for line in output.splitlines() if not line.startswith("Next Page Token =")
            ).strip()
            rows = [] if rows_text == "Not found" else json.loads(rows_text)
            if any(row["ref"] == kernel for row in rows):
                return True
            if len(rows) < 200:
                return False
            page += 1

    def collect(
        self,
        kernel: str,
        filename: str,
        receive: Callable[[Path], object],
        *,
        timeout_s: float = 7200,
        require_version: bool = True,
    ) -> str:
        parts = kernel.split("/")
        if (
            len(parts) not in (2, 3)
            or not all(parts)
            or (len(parts) == 3 and (not parts[2].isdigit() or int(parts[2]) < 1))
        ):
            raise ValueError("Kernel must be OWNER/SLUG or OWNER/SLUG/VERSION")
        if require_version and len(parts) != 3:
            raise ValueError("A shared inference kernel requires the submitted version")
        if Path(filename).name != filename:
            raise ValueError("Output filename must be a basename")
        started = self.monotonic()
        progress = {"kernel": kernel, "status": "waiting_for_artifacts"}
        while self.monotonic() - started < timeout_s:
            try:
                status = self.command(["kaggle", "kernels", "status", kernel], "kaggle-status.txt")
                progress.update(
                    remote_status=status.strip(), checked_utc=datetime.now(UTC).isoformat()
                )
                terminal = re.search(
                    r"has status [\"']?(?:KernelWorkerStatus\.)?"
                    r"(COMPLETE|ERROR|CANCELLED|CANCELED|CANCEL)\b",
                    status,
                )
            except (RuntimeError, subprocess.TimeoutExpired) as exc:
                progress["observation_error"] = str(exc)
                terminal = None
            atomic_write_json(self.directory / "remote.json", progress)
            if terminal:
                break
            self.sleep(30)
        else:
            raise TimeoutError("Artifact observation timed out; remote job was not cancelled")
        cache = self.root / ".cache"
        cache.mkdir(parents=True, exist_ok=True)
        # A fresh directory prevents an earlier download from satisfying this job.
        with tempfile.TemporaryDirectory(prefix="kaggle-output-", dir=cache) as temporary:
            self.command(
                [
                    "kaggle",
                    "kernels",
                    "output",
                    kernel,
                    "-p",
                    temporary,
                    "--file-pattern",
                    f"^{re.escape(filename)}$",
                    "--page-size",
                    "200",
                    "--quiet",
                    "--force",
                ],
                "download.log",
            )
            archive = Path(temporary) / filename
            if not archive.is_file():
                raise RuntimeError(f"Remote job ended without {filename}")
            receive(archive)
        outcome = terminal[1]
        atomic_write_json(self.directory / "remote.json", {**progress, "status": "collected"})
        return outcome
