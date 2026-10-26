"""Deterministic entity training data; held-out questions are authored in test.jsonl.

The checked-in templates are the generator's input. A family groups every alias
and phrasing of the same filled SQL, and is assigned before rendering text.
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from functools import cache
from pathlib import Path

from eth_nl2sql.config import read_jsonl, sha256_file, write_json, write_jsonl
from eth_nl2sql.data.leakage import family_split, leaked_ids
from eth_nl2sql.generation.retrieval import normalize_question
from eth_nl2sql.linking.validation import read_dictionary
from eth_nl2sql.validation import parse_query

SOURCE = "t05:entity-templates-v1"
STYLES = ("formal", "conversational", "abbreviated", "alternative")
WINDOWS = (
    ("2026-06-02", "2026-06-03"),
    ("2026-06-09", "2026-06-11"),
    ("2026-06-16", "2026-06-19"),
    ("2026-06-23", "2026-06-27"),
)


@cache
def canonical_sql(sql: str) -> str:
    return parse_query(sql).sql(dialect="bigquery", normalize_functions="upper", normalize=True)


def _alias(owner: str, aliases: dict) -> str:
    # Only unambiguous aliases; bare "uniswap" deliberately has three owners.
    choices = sorted(
        alias
        for alias, target in aliases.items()
        if target == owner and alias.casefold() != owner.casefold()
    )
    return choices[0] if choices else owner


def render_training(templates: list[dict], dictionary: Path) -> dict[str, list[dict]]:
    entities, aliases, _ = read_dictionary(dictionary)
    owners = sorted({row["owner"] for row in entities if row["category"] != "token_contract"})
    categories = sorted(
        {row["category"] for row in entities if row["category"] != "token_contract"}
    )
    records = {"train": [], "dev": []}
    for template in templates:
        targets = categories if template["target_kind"] == "category" else owners
        for index, target in enumerate(targets):
            start, end = WINDOWS[index % len(WINDOWS)]
            owner_b = owners[(index + 7) % len(owners)]
            fill = {
                "owner": target,
                "owner_b": owner_b,
                "category": target,
                "category_b": categories[(index + 1) % len(categories)],
                "start_date": start,
                "end_date": end,
                "n": 12,
            }
            # All parameters are selected from the validated local dictionary.
            sql_fill = {
                k: v.replace("'", "''") if isinstance(v, str) else v for k, v in fill.items()
            }
            sql = template["sql_template"].format(**sql_fill)
            canonical = canonical_sql(sql)
            family = "entity-v1-" + hashlib.sha256(canonical.encode()).hexdigest()[:16]
            split = "dev" if family_split(family) == "development" else "train"
            for style, seed in zip(STYLES, template["nl_seeds"], strict=True):
                nl_fill = {**fill, "entity": target, "entity_b": owner_b}
                if style in {"conversational", "alternative"}:
                    nl_fill["entity"] = _alias(target, aliases)
                    nl_fill["entity_b"] = _alias(owner_b, aliases)
                records[split].append(
                    {
                        "id": f"{family}__en__{style}",
                        "family_id": family,
                        "template_id": template["id"],
                        "style": style,
                        "source": SOURCE,
                        "subset": "entity",
                        "question": seed.format(**nl_fill),
                        "sql": sql,
                    }
                )
    # Small class strata can hash entirely into train. Keep at least one whole
    # family per template on dev, without splitting aliases or paraphrases.
    for template in templates:
        if not any(r["template_id"] == template["id"] for r in records["dev"]):
            family = min(
                r["family_id"] for r in records["train"] if r["template_id"] == template["id"]
            )
            records["dev"].extend(r for r in records["train"] if r["family_id"] == family)
            records["train"] = [r for r in records["train"] if r["family_id"] != family]
    return records


def build_entity_data(data_dir: Path, dictionary: Path) -> dict:
    """Replace only this generator's rows, retaining imported train/dev and test."""
    templates_path = data_dir / "templates" / "entity_templates.json"
    templates = json.loads(templates_path.read_text())
    generated = render_training(templates, dictionary)
    test = read_jsonl(data_dir / "test.jsonl")
    held_out = [row["question"] for row in test]
    test_sql = {canonical_sql(row["sql"]) for row in test}
    blocked_families = set()
    for rows in generated.values():
        leaked = set(leaked_ids(rows, held_out))
        blocked_families.update(
            row["family_id"]
            for row in rows
            if row["id"] in leaked or canonical_sql(row["sql"]) in test_sql
        )
    for split, rows in generated.items():
        generated[split] = [r for r in rows if r["family_id"] not in blocked_families]
        original = [r for r in read_jsonl(data_dir / f"{split}.jsonl") if r.get("source") != SOURCE]
        write_jsonl(data_dir / f"{split}.jsonl", original + generated[split])
    manifest = {
        "version": 1,
        "source": SOURCE,
        "seed": 42,
        "split_unit": "canonical filled SQL (all aliases and styles together)",
        "minimum_dev_families_per_template": 1,
        "windows_utc_half_open": WINDOWS,
        "styles": STYLES,
        "templates_sha256": sha256_file(templates_path),
        "dictionary_manifest_sha256": sha256_file(dictionary / "manifest.json"),
        "removed_families_for_test_overlap": sorted(blocked_families),
        "generated": {
            s: {
                "rows": len(rows),
                "families": len({r["family_id"] for r in rows}),
                "templates": sorted({r["template_id"] for r in rows}),
            }
            for s, rows in generated.items()
        },
        "files": {
            f"{s}.jsonl": sha256_file(data_dir / f"{s}.jsonl") for s in ("train", "dev", "test")
        },
    }
    write_json(data_dir / "entity-manifest.json", manifest)
    return manifest


def split_audit(splits: dict[str, list[dict]]) -> dict:
    """Distinguish held-out leakage from shared template boilerplate."""
    pairs = {}
    for left, right in (("train", "dev"), ("train", "test"), ("dev", "test")):
        a, b = splits[left], splits[right]
        left_sql = {canonical_sql(r["sql"]) for r in a}
        right_sql = {canonical_sql(r["sql"]) for r in b}
        left_families = {r["family_id"] for r in a if "family_id" in r}
        right_families = {r["family_id"] for r in b if "family_id" in r}
        exact = {normalize_question(r["question"]) for r in a} & {
            normalize_question(r["question"]) for r in b
        }
        shared = sorted(left_sql & right_sql)
        pairs[f"{left}/{right}"] = {
            "normalized_question_overlap": sorted(exact),
            "canonical_sql_overlap_count": len(shared),
            "canonical_sql_overlap_sha256": [
                hashlib.sha256(s.encode()).hexdigest() for s in shared
            ],
            "family_overlap": sorted(left_families & right_families),
            "ngram_12_overlap_ids": leaked_ids(a, [r["question"] for r in b]),
        }
    locations = defaultdict(list)
    for split, rows in splits.items():
        for row in rows:
            locations[row["id"]].append(split)
    duplicates = {key: value for key, value in locations.items() if len(value) > 1}
    passed = not duplicates and all(
        not (
            p["normalized_question_overlap"]
            or p["canonical_sql_overlap_count"]
            or p["family_overlap"]
            or (name != "train/dev" and p["ngram_12_overlap_ids"])
        )
        for name, p in pairs.items()
    )
    return {
        "passed": passed,
        "duplicate_ids": duplicates,
        "pairs": pairs,
        "policy": "No exact question/SQL/family overlaps; no 12-token overlaps with test. "
        "Train/dev share template boilerplate, reported separately.",
    }
