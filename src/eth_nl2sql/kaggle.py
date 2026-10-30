"""Kaggle deployment names shared by notebook builders and continuation."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path

from eth_nl2sql.config import ROOT


@dataclass(frozen=True)
class KaggleSettings:
    owner: str
    run_tag: str
    environment_cache: str

    @property
    def cache_kernel(self) -> str:
        return f"{self.owner}/{self.environment_cache}"

    def kernel(self, task: str, job: str | None = None) -> str:
        suffix = f"-{job}" if job else ""
        return f"{self.owner}/eth-nl2sql-{task}{suffix}-{self.run_tag}"


def load_settings(path: Path | None = None) -> KaggleSettings:
    with (path or ROOT / "configs/kaggle.toml").open("rb") as handle:
        values = tomllib.load(handle)
    return KaggleSettings(
        **{
            key: os.environ.get(f"ETH_NL2SQL_KAGGLE_{key.upper()}", value)
            for key, value in values.items()
        }
    )
