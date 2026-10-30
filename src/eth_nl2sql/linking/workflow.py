"""Build linking pipelines and bind cached predictions to their inputs."""

from __future__ import annotations

import json
from pathlib import Path

from eth_nl2sql import config as cfg


def build_pipeline(dictionary_dir: Path, *, use_encoder: bool, variant: str = "full"):
    from eth_nl2sql.linking.context import LinkingPipeline
    from eth_nl2sql.linking.dictionary import load_dictionary
    from eth_nl2sql.linking.entity import EntityLinker
    from eth_nl2sql.linking.schema import SchemaLinker

    encoder = None
    if use_encoder:
        from eth_nl2sql.generation.retrieval import load_encoder

        encoder = load_encoder(cfg.load())
    dictionary = load_dictionary(dictionary_dir)
    catalog = json.loads(cfg.CATALOG_PATH.read_text())
    synonyms = json.loads(cfg.SYNONYMS_PATH.read_text())
    return LinkingPipeline(
        dictionary,
        SchemaLinker(catalog, synonyms, encoder),
        EntityLinker(dictionary, encoder),
        variant=variant,
    )


def linking_path(split: str, variant: str = "full") -> Path:
    directory = cfg.DATA_DIR / "linking"
    return directory / (f"{split}.jsonl" if variant == "full" else f"{variant}/{split}.jsonl")


def linking_provenance(dictionary: Path, use_encoder: bool) -> dict:
    return {
        "dictionary": {p.name: cfg.sha256_file(p) for p in sorted(dictionary.glob("*.json"))},
        "catalog_sha256": cfg.sha256_file(cfg.CATALOG_PATH),
        "synonyms_sha256": cfg.sha256_file(cfg.SYNONYMS_PATH),
        "encoder": cfg.load()["models"]["encoder"] if use_encoder else None,
        "code": {
            p.name: cfg.sha256_file(p)
            for p in sorted((cfg.ROOT / "src/eth_nl2sql/linking").glob("*.py"))
        },
    }


def save_linkings(split: str, variant: str, rows: list[dict], provenance: dict) -> Path:
    path = linking_path(split, variant)
    cfg.write_jsonl(path, rows)
    cfg.write_json(
        path.with_suffix(".manifest.json"),
        {
            **provenance,
            "split": split,
            "variant": variant,
            "predictions_sha256": cfg.sha256_file(path),
        },
    )
    return path


def check_linking_manifest(path: Path, split: str, variant: str, dictionary: Path) -> dict:
    manifest_path = path.with_suffix(".manifest.json")
    if not manifest_path.exists():
        raise ValueError(f"Missing linking manifest {manifest_path}; rerun link")
    manifest = json.loads(manifest_path.read_text())
    current = linking_provenance(dictionary, use_encoder=False)
    if (
        any(
            manifest.get(k) != current[k]
            for k in ("dictionary", "catalog_sha256", "synonyms_sha256")
        )
        or manifest.get("predictions_sha256") != cfg.sha256_file(path)
        or any(manifest.get(k) != value for k, value in (("split", split), ("variant", variant)))
    ):
        raise ValueError(f"Stale linking manifest/dictionary/schema in {path}; rerun link")
    return manifest


def load_linkings(split: str, variant: str = "full", cases: list[dict] | None = None) -> dict:
    from eth_nl2sql.linking.context import Linking

    path = linking_path(split, variant)
    if not path.exists():
        raise ValueError(f"missing {path}; run `eth-nl2sql link --split {split}` first")
    rows = cfg.read_jsonl(path)
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError(f"Duplicate linking IDs in {path}")
    if cases is not None:
        questions = {c["id"]: c["question"] for c in cases}
        if {r["id"]: r.get("question") for r in rows} != questions:
            raise ValueError(f"Stale linking questions/IDs in {path}; rerun link")
    if path.with_suffix(".manifest.json").exists():
        check_linking_manifest(path, split, variant, cfg.DICTIONARY_DIR)
    return {row["id"]: Linking.from_json(row["linking"]) for row in rows}
