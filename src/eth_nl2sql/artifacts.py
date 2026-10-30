"""Stable content hashes and JSON artifact I/O."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Iterable
from pathlib import Path


def sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def json_digest(value: object) -> str:
    return text_digest(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    )


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def atomic_write_json(path: Path, value: object, *, durable: bool = False) -> None:
    """Replace a whole JSON artifact; optionally sync the file and directory journal."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            if durable:
                handle.flush()
                os.fsync(handle.fileno())
        temporary.replace(path)
        if durable:
            descriptor = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def ensure_output_paths(
    outputs: Iterable[Path],
    inputs: Iterable[Path],
    *,
    message: str,
) -> None:
    """Reject output collisions, including aliases of protected files in input trees."""
    protected = set()
    for path in inputs:
        protected.add(path.resolve())
        if path.is_dir():
            protected.update(p.resolve() for p in path.rglob("*") if p.is_file())
    destinations = [p.resolve() for p in outputs]
    if any(path in protected for path in destinations):
        raise ValueError(message)
    if len(set(destinations)) != len(destinations):
        raise ValueError("JSON and Markdown report paths must be different")
