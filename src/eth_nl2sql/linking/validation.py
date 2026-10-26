"""Validate address labels and the owner/alias/concept graph before use."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def _date(value: object, label: str) -> date:
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
        return parsed
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an ISO date (YYYY-MM-DD)") from exc


def validate_entities(entities: list[dict]) -> None:
    """Shared checks for both the linker and DuckDB label ingestion, including v1."""
    if not isinstance(entities, list) or not entities:
        raise ValueError("entities must be a nonempty list")
    addresses = set()
    for row in entities:
        if not isinstance(row, dict):
            raise ValueError("each entity must be an object")
        address = row.get("address")
        if not isinstance(address, str) or not re.fullmatch(r"0x[0-9a-fA-F]{40}", address):
            raise ValueError(f"invalid Ethereum address: {address!r}")
        address = address.lower()
        if address in addresses:
            raise ValueError(f"duplicate label address {address}")
        addresses.add(address)
        if row.get("address_lower") != address:
            raise ValueError(f"address_lower differs from address: {address}")
        if type(row.get("chain_id")) is not int or row["chain_id"] != 1:
            raise ValueError(f"only Ethereum mainnet chain_id=1 is supported: {address}")
        for field in ("owner", "primary_label", "category", "concept_class", "address_role"):
            _text(row.get(field), f"{address}.{field}")
        if row.get("confidence") not in {"high", "medium", "low"}:
            raise ValueError(f"invalid confidence: {address}")
        if not isinstance(row.get("aliases"), list):
            raise ValueError(f"aliases must be a list: {address}")
        for alias in row["aliases"]:
            _text(alias, f"{address}.alias")
        verified = _date(row.get("verified_date"), f"{address}.verified_date")
        if not isinstance(row.get("sources"), list) or not row["sources"]:
            raise ValueError(f"sources must be a nonempty list: {address}")
        for source in row["sources"]:
            if not isinstance(source, dict):
                raise ValueError(f"source must be an object: {address}")
            for field in ("name", "url", "revision", "locator", "note"):
                _text(source.get(field), f"{address}.source.{field}")
            url = urlparse(source["url"])
            if url.scheme not in {"http", "https"} or not url.netloc:
                raise ValueError(f"invalid source URL: {address}")
            if _date(source.get("retrieved_date"), "source.retrieved_date") > verified:
                raise ValueError(f"source retrieved after verified_date: {address}")


def validate_graph(entities: list[dict], aliases: dict, concepts: dict, *, strict: bool) -> None:
    from eth_nl2sql.linking.dictionary import normalize_phrase

    validate_entities(entities)
    if not isinstance(aliases, dict) or not isinstance(concepts, dict):
        raise ValueError("aliases and concepts must be objects")
    rows_by_owner = defaultdict(list)
    for row in entities:
        rows_by_owner[row["owner"]].append(row)
    normalized = {}
    for phrase, values in aliases.items():
        key = normalize_phrase(_text(phrase, "alias"))
        owners = [values] if isinstance(values, str) else values
        if not isinstance(owners, list) or not owners or any(
            not isinstance(owner, str) or owner not in rows_by_owner for owner in owners
        ):
            raise ValueError(f"alias {phrase!r} points to unknown owner(s): {values!r}")
        if key in normalized and normalized[key] != set(owners):
            raise ValueError(f"conflicting normalized alias: {phrase!r}")
        normalized[key] = set(owners)
    for key, info in concepts.items():
        _text(key, "concept key")
        if not isinstance(info, dict):
            raise ValueError(f"concept must be an object: {key}")
        _text(info.get("description"), f"{key}.description")
        ontology = _text(info.get("ontology_class"), f"{key}.ontology_class")
        concept_class = ontology.rsplit("/", 1)[-1].rsplit("#", 1)[-1]
        if not isinstance(info.get("aliases"), list):
            raise ValueError(f"concept aliases must be a list: {key}")
        for alias in info["aliases"]:
            _text(alias, f"{key}.alias")
        instances = info.get("instances")
        if not isinstance(instances, list) or any(
            not isinstance(owner, str) or owner not in rows_by_owner for owner in instances
        ):
            raise ValueError(f"concept {key!r} has unknown instances")
        if strict:
            expected = {
                r["owner"] for r in entities
                if r["category"] == key and r["concept_class"] == concept_class
            }
            if set(instances) != expected or len(instances) != len(set(instances)):
                raise ValueError(f"concept {key!r} instances differ from address labels")
    if not strict:
        return
    owner_names = defaultdict(set)
    for owner, rows in rows_by_owner.items():
        key = normalize_phrase(owner)
        # Different tokens can have names differing only in case. Preserve an
        # explicit ambiguous alias instead of merging their canonical owners.
        owner_names[key].add(owner)
        if owner != owner.strip() or len({(r['category'], r['concept_class']) for r in rows}) != 1:
            raise ValueError(f"inconsistent owner category/class: {owner!r}")
        for row in rows:
            info = concepts.get(row["category"])
            if info is None or owner not in info["instances"]:
                raise ValueError(f"owner {owner!r} missing from its concept")
            if (row["address_role"] == "token") != (row["category"] == "token_contract"):
                raise ValueError(f"token/operational role mismatch: {owner!r}")
            # Alias arrays are also consumed by the managed SQL layer. Require
            # the explicit map to include every row's aliases and canonical name.
            for phrase in [owner, *row["aliases"]]:
                if owner not in normalized.get(normalize_phrase(phrase), set()):
                    raise ValueError(f"alias map differs from row aliases: {phrase!r}, {owner!r}")
    for phrase, owners in normalized.items():
        if not owner_names[phrase].issubset(owners):
            raise ValueError(f"alias shadows canonical owner: {phrase!r}")
        for owner in owners:
            if not all(
                phrase in {normalize_phrase(a) for a in [owner, *row["aliases"]]}
                for row in rows_by_owner[owner]
            ):
                raise ValueError(f"alias missing from address labels: {phrase!r}, {owner!r}")


def read_dictionary(directory: Path) -> tuple[list[dict], dict, dict]:
    entities, aliases, concepts = (
        json.loads((directory / filename).read_text())
        for filename in ("entities.json", "aliases.json", "concepts.json")
    )
    manifest_path = directory / "manifest.json"
    strict = False
    if manifest_path.exists():
        from eth_nl2sql.config import sha256_file

        manifest = json.loads(manifest_path.read_text())
        if manifest.get("version") != 2:
            raise ValueError("unsupported dictionary manifest version")
        strict = True
        for filename in ("entities.json", "aliases.json", "concepts.json"):
            if sha256_file(directory / filename) != manifest.get("files", {}).get(filename):
                raise ValueError(f"dictionary checksum mismatch: {filename}")
        for source in manifest.get("sources", {}).values():
            if "snapshot" in source:
                snapshot = directory / source["snapshot"]
                if not snapshot.resolve().is_relative_to(directory.resolve()):
                    raise ValueError("source snapshot escapes dictionary directory")
                if sha256_file(snapshot) != source["sha256"]:
                    raise ValueError(f"source snapshot checksum mismatch: {source['snapshot']}")
    validate_graph(entities, aliases, concepts, strict=strict)
    return entities, aliases, concepts
