"""The authored draft is complete and isolated; no test invokes prediction generation."""

from collections import Counter

from eth_nl2sql.config import DATA_DIR, DICTIONARY_DIR, read_jsonl
from eth_nl2sql.data.annotations import GROUPS, PROPERTY_COUNTS, validate_review
from eth_nl2sql.data.benchmark import audit_benchmark
from eth_nl2sql.results import sql_signatures
from eth_nl2sql.validation import validate_sql

DIRECTORY = DATA_DIR / "benchmark/v2"


def test_t09a_complete_balanced_independent_draft():
    report = audit_benchmark(DIRECTORY, DATA_DIR, DICTIONARY_DIR)
    assert report["passed"], report
    assert report["status"] == "draft"
    assert report["case_count"] == 100
    assert report["primary_counts"] == dict.fromkeys(GROUPS, 20)
    assert report["property_counts"] == PROPERTY_COUNTS
    assert report["annotations"]["review_counts"] == {"pending": 100}
    assert not report["annotations"]["human_review_complete"]
    assert not report["release_ready"]
    assert "independent human review is incomplete" in report["release_blockers"]
    assert (
        "full snapshot execution is required before freezing; sample is development only"
        in (report["release_blockers"])
    )


def test_t09a_does_not_reuse_old_sql_with_only_literals_or_aliases_changed():
    cases = read_jsonl(DIRECTORY / "test.jsonl")
    structures = {sql_signatures(c["sql"])[1] for c in cases}
    assert len(structures) == 100
    for split in ("train", "dev", "dev_eval"):
        old = read_jsonl(DATA_DIR / f"{split}.jsonl")
        assert not structures & {sql_signatures(c["sql"])[1] for c in old}
    assert all(
        c["provenance"]
        == {"author": "codex-t09a", "author_type": "agent", "method": "independent_authoring"}
        for c in cases
    )


def test_t09a_review_and_property_diagnostics_cover_every_authored_case():
    cases = {c["id"]: c for c in read_jsonl(DIRECTORY / "test.jsonl")}
    annotations = {a["id"]: a for a in read_jsonl(DIRECTORY / "annotations.jsonl")}
    reviews = read_jsonl(DIRECTORY / "reviews.jsonl")
    notes = read_jsonl(DIRECTORY / "author-notes.jsonl")
    assert set(cases) == {r["id"] for r in reviews} == {n["id"] for n in notes}
    for review in reviews:
        assert not validate_review(cases[review["id"]], annotations[review["id"]], review)
        assert review["reviewer"] is None and review["reviewer_kind"] is None
        assert review["reviewed_at"] is None and review["status"] == "pending"
    contrasts = read_jsonl(DIRECTORY / "property-contrasts.jsonl")
    assert {c["id"] for c in contrasts} == {
        c["id"] for c in cases.values() if c["primary_group"] == "ambiguous_property"
    }
    assert dict(Counter(c["focus"] for c in contrasts)) == PROPERTY_COUNTS
    for contrast in contrasts:
        validate_sql(contrast["sql"])
        assert contrast["sql"] != cases[contrast["id"]]["sql"]
