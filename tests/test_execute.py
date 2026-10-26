from decimal import Decimal

import pytest
from conftest import ETH, TETHER, P

from eth_nl2sql.store.execute import ExecutionError, execute, to_duckdb


def run(store, sql):
    return list(execute(store, sql).rows)


def test_rewrites_managed_names_and_reports_calls():
    duck, calls = to_duckdb(
        f"SELECT COUNT(*) AS n FROM `{P}.transaction_facts`(DATE '2026-06-01', "
        f"DATE '2026-06-08') AS t JOIN `{P}.entity_labels_v1` AS l ON t.to_address = l.address"
    )
    assert "nl2sparql" not in duck.lower()
    assert [name for name, _ in calls] == ["transaction_facts"]


def test_half_open_window_and_multi_address_owner(store):
    sql = (
        f"SELECT SUM(t.value_wei) AS received FROM `{P}.transaction_facts`(DATE '2026-06-01', "
        f"DATE '2026-06-08') AS t JOIN `{P}.entity_labels_v1` AS l ON t.to_address = l.address "
        "WHERE l.owner = 'Binance'"
    )
    # T1 + T2 reach two different Binance addresses; T4 on June 9 is outside the window.
    assert run(store, sql) == [(Decimal(3 * ETH),)]


def test_bigquery_numeric_wei_threshold_runs_on_nonempty_data(store):
    sql = (
        f"SELECT COUNT(*) AS n FROM `{P}.transaction_facts`"
        "(DATE '2026-06-01', DATE '2026-06-08') "
        "WHERE value_wei >= NUMERIC '1000000000000000000'"
    )
    assert run(store, sql) == [(2,)]


def test_numeric_cast_retains_nine_fractional_digits(store):
    sql = (
        "SELECT CAST('1000000000000000000.000000001' AS NUMERIC) AS amount "
        f"FROM `{P}.transaction_facts`(DATE '2026-06-01', DATE '2026-06-02')"
    )
    assert run(store, sql) == [(Decimal('1000000000000000000.000000001'),)]


def test_labeled_transactions_expose_owner_columns(store):
    sql = (
        f"SELECT from_owner, to_owner, COUNT(*) AS n FROM `{P}.labeled_transactions`"
        "(DATE '2026-06-01', DATE '2026-06-08') WHERE to_owner IS NOT NULL "
        "GROUP BY from_owner, to_owner ORDER BY n DESC, to_owner"
    )
    assert run(store, sql) == [
        (None, "Binance", 2),
        (None, "Tornado Cash", 1),
        ("Tornado Cash", "Uniswap V3", 1),
    ]


def test_token_transfers_use_latest_contract_row_and_decimals(store):
    sql = (
        f"SELECT token_symbol, is_erc20, SUM(normalized_amount) AS amount FROM "
        f"`{P}.token_transfer_facts`(DATE '2026-06-01', DATE '2026-06-08') GROUP BY 1, 2"
    )
    assert run(store, sql) == [("USDT", True, 3.5)]
    contract = run(
        store, f"SELECT address, is_erc20 FROM `{P}.contract_dimension`(DATE '2026-07-01')"
    )
    assert contract == [(TETHER, True)]


def test_bigquery_functions_are_transpiled(store):
    sql = (
        f"SELECT DATE(block_timestamp) AS day, COUNTIF(is_success) AS ok, "
        f"SAFE_DIVIDE(SUM(value_wei), COUNT(*)) AS avg_value FROM "
        f"`{P}.transaction_facts`(DATE '2026-06-01', DATE '2026-06-03') GROUP BY day ORDER BY day"
    )
    rows = run(store, sql)
    assert [(row[0].isoformat(), row[1]) for row in rows] == [("2026-06-01", 1), ("2026-06-02", 1)]


@pytest.mark.parametrize(
    ("window", "code"),
    [
        ("DATE '2026-04-01', DATE '2026-04-08'", "window_outside_snapshot"),
        ("DATE '2026-06-01', DATE '2026-07-15'", "window_invalid"),
        ("DATE '2026-06-08', DATE '2026-06-01'", "window_invalid"),
        ("TIMESTAMP '2026-06-01 00:00:00', DATE '2026-06-08'", "window_invalid"),
        ("DATE '2026-06-01'", "window_invalid"),
    ],
)
def test_windows_are_checked_even_when_no_rows_match(store, window, code):
    with pytest.raises(ExecutionError) as error:
        execute(store, f"SELECT COUNT(*) AS n FROM `{P}.transaction_facts`({window})")
    assert error.value.code == code


def test_computed_constant_windows_are_allowed(store):
    sql = (
        f"SELECT COUNT(*) AS n FROM `{P}.transaction_facts`(DATE '2026-06-01', "
        "DATE_ADD(DATE '2026-06-01', INTERVAL 7 DAY))"
    )
    assert run(store, sql) == [(5,)]


def test_unknown_column_is_a_compile_error(store):
    with pytest.raises(ExecutionError) as error:
        execute(
            store,
            f"SELECT start_date FROM `{P}.transaction_facts`(DATE '2026-06-01', DATE '2026-06-02')",
        )
    assert error.value.code == "compile_error"


def test_parameterized_relation_without_arguments_is_rejected(store):
    with pytest.raises(ExecutionError) as error:
        execute(store, f"SELECT COUNT(*) AS n FROM `{P}.transaction_facts`")
    assert error.value.code == "compile_error"
