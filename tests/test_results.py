from datetime import UTC, date, datetime
from decimal import Decimal

from eth_nl2sql.results import (
    answer_scores,
    is_order_sensitive,
    results_equal,
    row_digests,
    sql_signatures,
)

P = "nl2sparql-thesis.nl2sparql_analytics"

# Digests cross-checked against luanvan's `canonicalize_result` (they must stay
# byte-identical so local results can be compared with the BigQuery c03 digests).
VECTORS = [
    ((0,), "d66202788c2f9c3ede18d981d648df4870e2836881a1faadd4f7c4efa6c5ec84"),
    ((Decimal("1.500000000"),), "6e176ac4eaff79c1bbb617c64f6c1bf8f1646930f200d654fd302bee3ba8725c"),
    ((0.1,), "79a7642a5c92556009d7d542ca7d514ee5fb0d4fb867fcda89d886ec1c509aa4"),
    (("Binance", True), "43facff405084691be5b585df9f20704ee742b05fbf907cbb716e667e6a42cbb"),
    (
        (date(2026, 6, 1), datetime(2026, 6, 30, 23, 59, 59, 123456, tzinfo=UTC)),
        "7ffef212a18cfe6be371ae604990d36431185a4068ca9fcc9282af4c2561b45e",
    ),
    ((None, None), "73e1e6a2f8233fb30ed9057aedaf9953004f35cf54c51ef071b19dc8d4b3ecab"),
    ((["x", "y"],), "10c0362612f56139f6c85ec53a84387aa1f027777c9f28815202ec377d95e6d1"),
]


def test_row_digests_match_luanvan():
    rows = [row for row, _ in VECTORS]
    assert row_digests(rows) == tuple(digest for _, digest in VECTORS)


def test_numbers_compare_by_value_not_type():
    assert row_digests([(1,)]) == row_digests([(Decimal("1.000"),)]) == row_digests([(1.0,)])
    assert row_digests([(-0.0,)]) == row_digests([(0,)])


def test_float_rounding_only_when_requested():
    a, b = 0.1 + 0.2, 0.3
    assert row_digests([(a,)]) != row_digests([(b,)])
    assert row_digests([(a,)], float_digits=12) == row_digests([(b,)], float_digits=12)


def test_order_semantics_follow_the_gold_query():
    assert is_order_sensitive(f"SELECT owner FROM `{P}.entity_labels_v1` ORDER BY owner")
    assert not is_order_sensitive(f"SELECT owner FROM `{P}.entity_labels_v1`")
    gold, swapped = ("a", "b"), ("b", "a")
    assert results_equal(gold, swapped, gold_arity=1, predicted_arity=1, ordered=False)
    assert not results_equal(gold, swapped, gold_arity=1, predicted_arity=1, ordered=True)
    assert not results_equal(gold, gold, gold_arity=1, predicted_arity=2, ordered=False)


def test_answer_scores_use_multisets():
    assert answer_scores(["a", "b"], ["a"]) == (1.0, 0.5, 2 / 3)
    assert answer_scores([], []) == (1.0, 1.0, 1.0)
    assert answer_scores(["a"], []) == (0.0, 0.0, 0.0)


def test_structural_signature_ignores_aliases_and_literals():
    relation = f"`{P}.transaction_facts`"
    left = f"SELECT COUNT(*) AS n FROM {relation}(DATE '2026-06-01', DATE '2026-06-08') AS t"
    right = f"SELECT COUNT(*) AS c FROM {relation}(DATE '2026-06-08', DATE '2026-06-15') AS x"
    assert sql_signatures(left)[0] != sql_signatures(right)[0]
    assert sql_signatures(left)[1] == sql_signatures(right)[1]
