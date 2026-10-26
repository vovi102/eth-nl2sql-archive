import pytest

from eth_nl2sql.validation import ValidationError, validate_sql

P = "nl2sparql-thesis.nl2sparql_analytics"


@pytest.mark.parametrize(
    "sql",
    [
        f"SELECT COUNT(*) AS n FROM `{P}.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08')",
        f"SELECT owner FROM `{P}.entity_labels_v1` WHERE concept_class = 'DEXProtocol'",
        f"WITH t AS (SELECT to_address FROM `{P}.transaction_facts`(DATE '2026-06-01', "
        "DATE '2026-06-02')) SELECT COUNT(*) AS n FROM t",
    ],
)
def test_accepts_managed_read_only_queries(sql):
    validate_sql(sql)


@pytest.mark.parametrize(
    ("sql", "code"),
    [
        ("SELECT COUNT(*) FROM `bigquery-public-data.crypto_ethereum.transactions`", "unsafe"),
        (f"SELECT * FROM `{P}.entity_labels_v1`", "unsafe"),
        (f"SELECT owner FROM `{P}.entity_labels_v1`;", "unsafe"),
        (f"SELECT owner FROM `{P}.entity_labels_v1` -- hi", "unsafe"),
        (f"DELETE FROM `{P}.entity_labels_v1` WHERE TRUE", "unsafe"),
        ("SELECT 1 AS one", "unsafe"),
        ("SELECT FROM WHERE", "parse_error"),
        ("", "parse_error"),
        # Short relation names are not the managed objects (luanvan B1's main failure).
        ("SELECT COUNT(*) AS n FROM transaction_facts WHERE start_date = '2026-06-01'", "unsafe"),
    ],
)
def test_rejects_unsafe_or_unmanaged_sql(sql, code):
    with pytest.raises(ValidationError) as error:
        validate_sql(sql)
    assert error.value.code == code
