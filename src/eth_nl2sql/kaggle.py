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

    def _owned(self, slug: str) -> str:
        return slug if "/" in slug else f"{self.owner}/{slug}"

    @property
    def cache_kernel(self) -> str:
        return self._owned(self.environment_cache)

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
    for key in ("owner", "environment_cache", "inference_kernel"):
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
        record = {"kernel": kernel, "identity": identity, "status": "submitting"}
        atomic_write_json(receipt, record)
        # Never retry a push: a timeout can still have created a remote version.
        output = self.command(
            [
                "kaggle",
                "kernels",
                "push",
                "-p",
                str(notebook),
                "--accelerator",
                "NvidiaTeslaT4",
                "--timeout",
                "43200",
            ],
            "push.log",
            attempts=1,
        )
        match = re.search(r"Kernel version (\d+) successfully pushed", output)
        if match is None:
            raise RuntimeError("Push did not confirm a version; inspect push.log before retrying")
        reference = f"{kernel}/{int(match[1])}"
        atomic_write_json(receipt, {**record, "status": "submitted", "kernel_ref": reference})
        return reference

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
