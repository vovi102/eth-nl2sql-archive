"""Invariants of the committed dataset files."""

import re
from collections import Counter

from eth_nl2sql.cli import SPLITS
from eth_nl2sql.config import read_jsonl
from eth_nl2sql.data.entities import SOURCE
from eth_nl2sql.data.leakage import family_split, leaked_ids
from eth_nl2sql.store.build import connect, create_schema
from eth_nl2sql.store.execute import execute
from eth_nl2sql.store.snapshot import extraction_queries

TRAIN, DEV, TEST = (read_jsonl(SPLITS[name]) for name in ("train", "dev", "dev_eval"))


def test_split_sizes_and_unique_ids():
    assert (
        sum(r.get("source") != SOURCE for r in TRAIN),
        sum(r.get("source") != SOURCE for r in DEV),
    ) == (3604, 396)
    assert sum(r.get("source") == SOURCE for r in TRAIN + DEV) == 1388
    assert len(TEST) == 100
    ids = [row["id"] for row in TRAIN + DEV + TEST]
    assert len(ids) == len(set(ids))


def test_semantic_families_never_cross_splits():
    train_families = {row["family_id"] for row in TRAIN}
    dev_families = {row["family_id"] for row in DEV}
    assert not train_families & dev_families
    assert set(Counter(row["family_id"] for row in TRAIN).values()) == {4}


def test_no_test_question_leaks_into_training_data():
    assert leaked_ids(TRAIN + DEV, [row["question"] for row in TEST]) == []


def test_every_dataset_query_compiles_on_the_store_schema():
    con = connect()
    create_schema(con)
    for sql in {row["sql"] for row in TRAIN + DEV + TEST}:
        execute(con, sql)


def _skeleton(sql: str) -> str:
    sql = re.sub(r"'[^']*'", "'?'", sql)
    return " ".join(re.sub(r"\b\d+(\.\d+)?\b", "N", sql).split())


def test_generic_test_subset_covers_all_29_intents():
    generic = [row for row in TEST if row["subset"] == "generic"]
    assert len(generic) == 50
    assert len({_skeleton(row["sql"]) for row in generic}) == 29


def test_family_split_is_deterministic():
    assert family_split("syn-v2-000001") == family_split("syn-v2-000001")
    shares = Counter(family_split(f"fam-{i}") for i in range(2000))
    assert 0.07 < shares["development"] / 2000 < 0.13


def test_snapshot_extraction_reads_only_catalog_columns():
    queries = extraction_queries()
    assert len(queries) == 31 * 3 + 2
    assert all("input" not in query.sql.split("FROM")[0] for query in queries)
    assert queries[0].sql.endswith(
        "block_timestamp >= TIMESTAMP('2026-05-31') AND block_timestamp < TIMESTAMP('2026-06-01')"
    )
