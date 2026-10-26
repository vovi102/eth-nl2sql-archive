from conftest import P

from eth_nl2sql.evaluate import bootstrap_ci, evaluate_predictions, mcnemar_exact, summarize

GOLD_INFLOW = (
    f"SELECT SUM(t.value_wei) AS received FROM `{P}.transaction_facts`(DATE '2026-06-01', "
    f"DATE '2026-06-08') AS t JOIN `{P}.entity_labels_v1` AS l ON t.to_address = l.address "
    "WHERE l.owner = 'Binance'"
)
GOLD_TOP = (
    f"SELECT to_owner, COUNT(*) AS n FROM `{P}.labeled_transactions`(DATE '2026-06-01', "
    "DATE '2026-06-08') WHERE to_owner IS NOT NULL GROUP BY to_owner ORDER BY n DESC, to_owner"
)
CASES = [
    {
        "id": "inflow",
        "question": "q",
        "sql": GOLD_INFLOW,
        "subset": "entity",
        "specifics": ["multi_address"],
    },
    {
        "id": "top",
        "question": "q",
        "sql": GOLD_TOP,
        "subset": "entity",
        "specifics": ["class_level"],
    },
    {
        "id": "count",
        "question": "q",
        "sql": f"SELECT COUNT(*) AS n FROM `{P}.block_facts`(DATE '2026-06-01', DATE '2026-06-08')",
        "subset": "generic",
    },
]


def by_id(results):
    return {result.id: result for result in results}


def test_gold_echo_scores_perfectly(store):
    predictions = {case["id"]: {"raw_output": case["sql"], "latency_ms": 5.0} for case in CASES}
    results = evaluate_predictions(store, CASES, predictions)
    assert all(r.execution_match and r.exact_match and r.status == "ok" for r in results)
    assert summarize(results, samples=200)["execution_accuracy"] == 1.0


def test_equivalent_sql_matches_on_execution_not_text(store):
    # Lists Binance's addresses instead of filtering by owner, and renames the column.
    from conftest import BINANCE

    addresses = ", ".join(f"'{a}'" for a in BINANCE)
    alternative = (
        f"SELECT SUM(value_wei) AS total FROM `{P}.transaction_facts`(DATE '2026-06-01', "
        f"DATE '2026-06-08') WHERE to_address IN ({addresses})"
    )
    results = by_id(evaluate_predictions(store, CASES[:1], {"inflow": {"raw_output": alternative}}))
    assert results["inflow"].execution_match and not results["inflow"].exact_match


def test_failures_stay_in_the_denominator(store):
    predictions = {
        "inflow": {"raw_output": "I don't know."},
        "top": {
            "raw_output": f"SELECT to_owner, COUNT(*) AS n FROM `{P}.labeled_transactions`"
            "(DATE '2026-04-01', DATE '2026-04-08') GROUP BY to_owner"
        },
        # "count" has no prediction at all.
    }
    results = by_id(evaluate_predictions(store, CASES, predictions))
    assert results["inflow"].status == "no_sql"
    assert results["top"].status == "window_outside_snapshot"
    assert results["count"].status == "no_sql"
    summary = summarize(list(results.values()), samples=200)
    assert summary["execution_accuracy"] == 0.0
    assert summary["by_group"]["specific:multi_address"]["n"] == 1


def test_wrong_order_fails_an_ordered_gold(store):
    reversed_order = GOLD_TOP.replace("ORDER BY n DESC, to_owner", "ORDER BY n ASC, to_owner")
    results = by_id(
        evaluate_predictions(store, CASES[1:2], {"top": {"raw_output": reversed_order}})
    )
    assert results["top"].status == "ok" and not results["top"].execution_match
    assert 0 < results["top"].answer_f1 <= 1


def test_statistics():
    assert mcnemar_exact([True, True, False], [True, False, False]) == {
        "left_only": 1,
        "right_only": 0,
        "p_value": 1.0,
    }
    assert mcnemar_exact([True] * 10, [False] * 10)["p_value"] < 0.01
    assert bootstrap_ci([1.0, 0.0] * 50, samples=500) == bootstrap_ci([1.0, 0.0] * 50, samples=500)
