import pytest

from eth_nl2sql.generation.extract import extract_sql

SQL = "SELECT COUNT(*) AS n\nFROM `p.d.transaction_facts`(DATE '2026-06-01', DATE '2026-06-08')"


@pytest.mark.parametrize(
    ("raw", "format_ok"),
    [
        (SQL, True),
        (f"```sql\n{SQL}\n```", True),
        (f"{SQL};", False),
        (f"Here is the GoogleSQL query that answers the question:\n\n```\n{SQL}\n```", False),
        (f"{SQL}\n\nThis query counts the transactions in the window.", False),
        (f"{SQL}\n</google_sql>", False),
    ],
)
def test_extracts_the_query(raw, format_ok):
    assert extract_sql(raw) == (SQL, format_ok)


@pytest.mark.parametrize("raw", ["", "I cannot answer that.", "```\nno sql here\n```"])
def test_returns_none_without_a_query(raw):
    assert extract_sql(raw) == (None, False)


def test_keeps_multi_paragraph_queries():
    raw = "WITH t AS (\n  SELECT 1 AS x\n)\n\nSELECT x FROM t"
    assert extract_sql(raw) == (raw, True)
