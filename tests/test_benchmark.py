"""Benchmark isolation, linking gold integrity and release gates (all offline)."""

import copy
import json

import pyarrow as pa
import pytest
from conftest import USER, P, tx

from eth_nl2sql.cli import SPLITS, main
from eth_nl2sql.config import (
    DATA_DIR,
    DICTIONARY_DIR,
    read_jsonl,
    sha256_file,
    write_json,
    write_jsonl,
)
from eth_nl2sql.data.annotations import (
    GROUPS,
    annotation_digest,
    audit_annotations,
    draft_development_annotations,
    pending_review,
    sql_schema,
    validate_annotation,
    validate_review,
)
from eth_nl2sql.data.benchmark import (
    audit_benchmark,
    draft_manifest,
    freeze_benchmark,
    require_frozen,
)
from eth_nl2sql.data.entities import split_audit
from eth_nl2sql.linking.dictionary import load_dictionary, owner_id
from eth_nl2sql.store.build import LABEL_SCHEMA, connect, create_schema, label_rows


@pytest.fixture(scope="module")
def dictionary():
    return load_dictionary(DICTIONARY_DIR)


@pytest.fixture()
def development():
    cases = read_jsonl(DATA_DIR / "dev_eval.jsonl")
    annotations = read_jsonl(DATA_DIR / "dev_eval-annotations.jsonl")
    reviews = read_jsonl(DATA_DIR / "dev_eval-annotation-reviews.jsonl")
    return cases, annotations, reviews


@pytest.fixture()
def benchmark(tmp_path):
    data = tmp_path / "data"
    directory = data / "benchmark/v2"
    directory.mkdir(parents=True)
    for i, name in enumerate(("train", "dev", "dev_eval")):
        write_jsonl(
            data / f"{name}.jsonl",
            [
                {
                    "id": name,
                    "question": f"Training phrase {i}",
                    "family_id": name,
                    "sql": f"SELECT COUNT(*) FROM `{P}.entity_labels_v1` WHERE chain_id = {i + 2}",
                }
            ],
        )
    for name in ("test.jsonl", "annotations.jsonl", "reviews.jsonl"):
        write_jsonl(directory / name, [])
    write_json(directory / "manifest.json", draft_manifest(directory, data, DICTIONARY_DIR))
    return directory, data


def test_development_is_separate_and_original_bytes_are_preserved():
    assert SPLITS["dev_eval"] == DATA_DIR / "dev_eval.jsonl"
    assert SPLITS["test"] == DATA_DIR / "benchmark/v2/test.jsonl"
    assert sha256_file(SPLITS["dev_eval"]) == (
        "2e2f63071718e045d4ca24cea8aecbdaf37c7749d4f33ce3e2d687cd1173c8ee"
    )
    assert not (DATA_DIR / "test.jsonl").exists()


def test_all_development_annotations_validate_without_claiming_human_review(
    development, dictionary
):
    report = audit_annotations(*development, dictionary)
    assert report["passed"]
    assert report["review_counts"] == {"pending": 100}
    assert not report["human_review_complete"]


@pytest.mark.parametrize("field", ["question", "sql"])
def test_edits_invalidate_annotation_and_review(field, development, dictionary):
    cases, annotations, reviews = development
    cases[0][field] += " "
    assert f"stale {field} hash" in validate_annotation(cases[0], annotations[0], dictionary)
    assert f"stale review {field} hash" in validate_review(cases[0], annotations[0], reviews[0])


def test_annotation_edits_invalidate_review_and_key_order_does_not(development):
    cases, annotations, reviews = development
    original = annotations[50]
    assert annotation_digest(dict(reversed(list(original.items())))) == annotation_digest(original)
    original["properties"]["direction"][0]["value"] = "to"
    assert "stale review annotation hash" in validate_review(cases[50], original, reviews[50])


@pytest.mark.parametrize(
    "field, value",
    [
        ("primary_group", "alias"),
        ("difficulty", "hard"),
        ("specifics", ["alias"]),
        ("provenance", {"author": "changed"}),
    ],
)
def test_case_metadata_edits_invalidate_review(field, value, development):
    cases, annotations, reviews = development
    cases[0][field] = value
    assert "stale review case hash" in validate_review(cases[0], annotations[0], reviews[0])


@pytest.mark.parametrize(
    "mutation, expected",
    [
        (lambda a: a["entities"][0]["addresses"].pop(), "owner address set differs"),
        (lambda a: a["entities"][0].update(owner="Unknown owner"), "unknown owner"),
        (lambda a: a["entities"][0]["mention"].update(start=0), "mention span"),
        (
            lambda a: a["properties"]["direction"][0].update(target="entity:99"),
            "nonexistent target",
        ),
        (lambda a: a["properties"].update(fact="token_transfer"), "fact property"),
        (
            lambda a: a["schema"]["columns"].append({"relation": "bad", "column": "bad"}),
            "schema targets",
        ),
        (
            lambda a: a["properties"].update(
                address_role=[{"target": "entity:0", "value": "unknown"}]
            ),
            "not one of",
        ),
    ],
)
def test_bad_linking_targets_are_rejected(mutation, expected, development, dictionary):
    cases, annotations, _ = development
    mutation(annotations[50])
    assert any(expected in e for e in validate_annotation(cases[50], annotations[50], dictionary))


def test_class_members_are_dictionary_bound(development, dictionary):
    cases, annotations, _ = development
    annotations[88]["classes"][0]["owners"].pop()
    assert "class members differ from the frozen dictionary" in validate_annotation(
        cases[88], annotations[88], dictionary
    )


@pytest.mark.parametrize("part", [0, 1, 2])
def test_duplicate_and_missing_ids_fail(part, development, dictionary):
    rows = development[part]
    rows[0] = copy.deepcopy(rows[1])
    report = audit_annotations(*development, dictionary)
    assert not report["passed"]
    assert any("duplicate IDs" in e for e in report["issues"])


@pytest.mark.parametrize("part", [0, 1, 2])
def test_malformed_objects_fail_without_a_traceback(part, development, dictionary):
    development[part][0] = None
    assert not audit_annotations(*development, dictionary)["passed"]


def test_invalid_review_status_is_reported(development, dictionary):
    development[2][0]["status"] = []
    report = audit_annotations(*development, dictionary)
    assert not report["passed"]
    assert report["cases"][0]["review_status"] == "invalid"


def test_human_review_requires_identity_and_annotation_hash(development):
    cases, annotations, reviews = development
    review = reviews[0]
    review.update(status="human_reviewed", reviewer_kind="agent")
    errors = validate_review(cases[0], annotations[0], review)
    assert "completed review requires reviewer, timestamp and note" in errors
    assert "review status differs from reviewer kind" in errors
    review.update(
        reviewer="fixture-human",
        reviewer_kind="human",
        reviewed_at="2026-10-27T10:00:00Z",
        note="Synthetic test review",
    )
    assert validate_review(cases[0], annotations[0], review) == []
    cases[0]["provenance"] = {"author": "fixture-human"}
    assert "human review must be independent of the author" in validate_review(
        cases[0], annotations[0], review
    )


def test_schema_targets_resolve_ctes_aliases_and_count_star():
    query = (
        f"WITH t AS (SELECT to_owner, transaction_hash FROM `{P}.labeled_transactions`"
        "(DATE '2026-06-01', DATE '2026-06-08')) "
        "SELECT to_owner, COUNT(*) AS n FROM t GROUP BY to_owner ORDER BY n DESC"
    )
    result = sql_schema(query)
    assert result == {
        "relations": ["labeled_transactions"],
        "columns": [
            {"relation": "labeled_transactions", "column": "to_owner"},
            {"relation": "labeled_transactions", "column": "transaction_hash"},
        ],
    }
    assert sql_schema(f"SELECT COUNT(*) FROM `{P}.entity_labels_v1`")["columns"] == []


def test_leakage_checks_every_pair_including_old_evaluation_against_final():
    a = {
        "id": "a",
        "question": "old question",
        "family_id": "old",
        "sql": f"SELECT COUNT(*) FROM `{P}.entity_labels_v1`",
    }
    b = {**a, "id": "b", "question": "new wording", "family_id": "new"}
    report = split_audit({"train": [], "dev": [], "dev_eval": [a], "test": [b]})
    assert not report["passed"]
    assert len(report["pairs"]) == 6
    assert report["pairs"]["dev_eval/test"]["canonical_sql_overlap_count"] == 1


def test_draft_passes_infrastructure_checks_but_cannot_be_released(benchmark):
    directory, data = benchmark
    report = audit_benchmark(directory, data, DICTIONARY_DIR)
    assert report["passed"]
    assert not report["release_ready"]
    assert report["case_count"] == 0
    with pytest.raises(ValueError, match="not frozen"):
        require_frozen(directory, data, DICTIONARY_DIR)


@pytest.mark.parametrize("filename", ["test.jsonl", "annotations.jsonl", "reviews.jsonl"])
def test_file_hash_mismatch_fails(filename, benchmark):
    directory, data = benchmark
    (directory / filename).write_text("\n")
    report = audit_benchmark(directory, data, DICTIONARY_DIR)
    assert not report["passed"]
    assert any("checksum mismatch" in e for e in report["issues"])


def test_development_split_hash_is_part_of_final_benchmark(benchmark):
    directory, data = benchmark
    (data / "train.jsonl").write_text("[]\n")
    report = audit_benchmark(directory, data, DICTIONARY_DIR)
    assert not report["passed"]
    assert any("dependency hashes" in e for e in report["issues"])


@pytest.mark.parametrize("value", [None, [], {"status": []}])
def test_invalid_manifest_is_reported(value, benchmark):
    directory, data = benchmark
    write_json(directory / "manifest.json", value)
    report = audit_benchmark(directory, data, DICTIONARY_DIR)
    assert not report["passed"]
    assert not report["release_ready"]


def test_malformed_annotation_id_is_reported(benchmark):
    directory, data = benchmark
    write_jsonl(directory / "annotations.jsonl", [{"id": []}])
    write_json(directory / "manifest.json", draft_manifest(directory, data, DICTIONARY_DIR))
    assert not audit_benchmark(directory, data, DICTIONARY_DIR)["passed"]


def test_freeze_reports_invalid_structure_without_a_traceback(benchmark, store):
    directory, data = benchmark
    write_json(directory / "manifest.json", {"status": "draft"})
    with pytest.raises(ValueError, match="not release-ready"):
        freeze_benchmark(directory, data, DICTIONARY_DIR, store)


@pytest.mark.parametrize("known", [True, False])
def test_explicit_address_owner_is_required_only_when_known(dictionary, known):
    address = dictionary.by_id[owner_id("Binance")].addresses[0] if known else "0x" + "0" * 40
    case = {
        "id": "literal",
        "question": f"Count transactions for {address}",
        "sql": f"SELECT COUNT(*) FROM `{P}.entity_labels_v1`",
    }
    annotation = draft_development_annotations([case], dictionary)[0]
    start = case["question"].index(address)
    annotation["entities"] = [
        {
            "mention": {"text": address, "start": start, "end": start + len(address)},
            "owner": None,
            "addresses": [address],
            "address_scope": "explicit_address",
        }
    ]
    errors = validate_annotation(case, annotation, dictionary)
    assert bool(errors) == known
    if known:
        annotation["entities"][0]["owner"] = "Binance"
        assert validate_annotation(case, annotation, dictionary) == []


def test_cli_blocks_draft_test_before_model_loading_or_prediction_loading():
    for args in (
        ["echo-gold"],
        ["evaluate", "--config", "nonexistent"],
        ["prompts", "--config", "b2l"],
        ["generate", "--config", "b1"],
        ["link", "--no-encoder"],
        ["link", "--variant", "all", "--no-encoder"],
        ["link-experiments", "--no-encoder"],
        ["evaluate-linking"],
        ["report"],
    ):
        with pytest.raises(SystemExit, match="Final test v2 is not frozen"):
            main([*args, "--split", "test"])


def test_cli_human_gate_and_output_collision(tmp_path):
    with pytest.raises(SystemExit) as caught:
        main(["check-annotations", "--require-human", "--out", str(tmp_path / "audit.json")])
    assert caught.value.code == 1
    report = json.loads((tmp_path / "audit.json").read_text())
    assert report["passed"] and not report["human_review_complete"]
    path = DATA_DIR / "dev_eval-annotations.jsonl"
    original = path.read_bytes()
    with pytest.raises(SystemExit, match="must not overwrite"):
        main(["check-annotations", "--out", str(path)])
    assert path.read_bytes() == original


def _synthetic_release(directory, data, dictionary):
    """Generate test-only records and simulated human approvals; never touch project data."""
    cases, annotations, reviews = [], [], []
    for i in range(100):
        group = GROUPS[i // 20]
        name = "BNB exchange" if group == "alias" else "Binance"
        is_class = group == "class_level"
        target = "centralized exchange" if is_class else name
        predicate = "to_category = 'exchange'" if is_class else "to_owner = 'Binance'"
        case = {
            "id": f"fixture-{i}",
            "family_id": f"fixture-family-{i}",
            "question": f"Fixture {i}: count transactions received by {target} in the first week.",
            "sql": f"SELECT COUNT(*) FROM `{P}.labeled_transactions`"
            f"(DATE '2026-06-01', DATE '2026-06-08') WHERE {predicate} "
            f"AND transaction_index >= {i}",
            "primary_group": group,
            "specifics": [] if group == "generic" else [group],
            "subset": "generic" if group == "generic" else "entity",
            "difficulty": "easy",
            "categories": ["fixture"],
            "empty_reason": None,
            "window": {"start_date": "2026-06-01", "end_date": "2026-06-08"},
            "provenance": {
                "author": "fixture-agent",
                "author_type": "agent",
                "method": "independent_authoring",
            },
            "property_focus": None
            if group != "ambiguous_property"
            else "direction"
            if i < 87
            else "fact"
            if i < 94
            else "address_role",
        }
        expected = {"direction": "to", "owners": [] if is_class else ["Binance"]}
        if is_class:
            expected["category"] = "exchange"
        annotation = draft_development_annotations(
            [{**case, "entity_expectations": expected}], dictionary
        )[0]
        review = pending_review(case, annotation)
        review.update(
            status="human_reviewed",
            reviewer="fixture-human",
            reviewer_kind="human",
            reviewed_at="2026-10-27T10:00:00Z",
            note="Simulated approval for test only",
        )
        cases.append(case)
        annotations.append(annotation)
        reviews.append(review)
    for filename, rows in zip(
        ("test.jsonl", "annotations.jsonl", "reviews.jsonl"),
        (cases, annotations, reviews),
        strict=True,
    ):
        write_jsonl(directory / filename, rows)
    write_json(directory / "manifest.json", draft_manifest(directory, data, DICTIONARY_DIR))


def test_freeze_checks_execution_sample_scope_and_immutability(benchmark, dictionary):
    directory, data = benchmark
    _synthetic_release(directory, data, dictionary)
    with connect() as con:
        create_schema(con)
        rows = label_rows(DICTIONARY_DIR / "entities.json")
        con.register(
            "fixture_labels",
            pa.Table.from_pylist([dict(zip(LABEL_SCHEMA, row, strict=True)) for row in rows]),
        )
        con.execute("INSERT INTO entity_labels_snapshot SELECT * FROM fixture_labels")
        addresses = dictionary.by_id[owner_id("Binance")].addresses[:2]
        con.executemany(
            "INSERT INTO transactions VALUES (" + ", ".join("?" * 14) + ")",
            [tx(f"0xFIXTURE{i}", USER, a, 1, day=2, index=1000) for i, a in enumerate(addresses)],
        )
        profile = {
            "scope": "test_fixture",
            "complete_snapshot": False,
            "labels_sha256": sha256_file(DICTIONARY_DIR / "entities.json"),
            "parquet_manifest_sha256": "0" * 64,
        }
        con.execute("INSERT INTO store_metadata VALUES ('profile', ?)", [json.dumps(profile)])
        report = audit_benchmark(directory, data, DICTIONARY_DIR, con)
        assert report["passed"], report
        assert all(c["passed"] for c in report["gold"])
        assert not report["release_ready"]
        with pytest.raises(ValueError, match="not release-ready"):
            freeze_benchmark(directory, data, DICTIONARY_DIR, con)
        # Simulated full-snapshot metadata exercises the release transition only.
        profile.update(complete_snapshot=True)
        con.execute("UPDATE store_metadata SET value=? WHERE key='profile'", [json.dumps(profile)])
        frozen = freeze_benchmark(directory, data, DICTIONARY_DIR, con)
        assert frozen["status"] == "frozen" and frozen["frozen_at"]
        assert require_frozen(directory, data, DICTIONARY_DIR)["status"] == "frozen"
        original = (directory / "manifest.json").read_bytes()
        with pytest.raises(ValueError, match="already frozen"):
            freeze_benchmark(directory, data, DICTIONARY_DIR, con)
        with pytest.raises(ValueError, match="already frozen"):
            draft_manifest(directory, data, DICTIONARY_DIR)
        assert (directory / "manifest.json").read_bytes() == original
