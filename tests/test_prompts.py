import json

import pytest

from eth_nl2sql.config import CATALOG_PATH
from eth_nl2sql.generation.prompt import build_messages, catalog_summary, compact_schema
from eth_nl2sql.generation.runs import CONFIGS, prompt_rows, training_rows
from eth_nl2sql.linking.context import Linking
from eth_nl2sql.linking.resolver import Resolution

CATALOG = json.loads(CATALOG_PATH.read_text())
P = "nl2sparql-thesis.nl2sparql_analytics"


def test_catalog_summary_shows_callable_qualified_relations():
    summary = catalog_summary(CATALOG)
    assert f"`{P}.transaction_facts`(start_date DATE, end_date DATE)" in summary
    assert f"`{P}.entity_labels_v1` (view)" in summary
    assert "input" not in summary.split("APPROVED JOINS")[0]
    assert len(summary) < 12_000


def test_compact_schema_lists_all_eight_relations():
    assert len(compact_schema(CATALOG).splitlines()) == 8


def test_messages_put_examples_and_linking_before_the_question():
    messages = build_messages(
        "How many?",
        system="sys",
        examples=[{"question": "Q1", "sql": "S1"}],
        linking="Linking hints",
    )
    user = messages[1]["content"]
    assert user.index("Examples:") < user.index("Linking hints") < user.index("Question: How many?")
    assert user.endswith("SQL:")


LINKING = Linking(
    ("transaction_facts",),
    ("transaction_facts.to_address",),
    (Resolution("Binance", "instance", "to", "Binance", "ExchangeAccount", ("0x1", "0x2"), ()),),
)
CASES = [{"id": "q1", "question": "How much ETH did Binance receive?", "sql": "SELECT 1 AS one"}]


def test_linking_config_renders_owner_filter():
    rows = prompt_rows(CONFIGS["b1l"], CASES, catalog=CATALOG, linkings={"q1": LINKING})
    content = rows[0]["messages"][1]["content"]
    assert "entity_labels_v1.owner = 'Binance'" in content
    assert "2 labeled addresses" in content


def test_linking_config_requires_linking_results():
    with pytest.raises(ValueError):
        prompt_rows(CONFIGS["b1l"], CASES, catalog=CATALOG)


def test_few_shot_needs_exactly_five_examples():
    with pytest.raises(ValueError):
        prompt_rows(CONFIGS["b2"], CASES, catalog=CATALOG, retrieve=lambda case: [])
    shots = [{"id": f"e{i}", "question": f"Q{i}", "sql": f"S{i}"} for i in range(5)]
    rows = prompt_rows(CONFIGS["b2"], CASES, catalog=CATALOG, retrieve=lambda case: shots)
    assert rows[0]["example_ids"] == [f"e{i}" for i in range(5)]


def test_training_rows_use_the_compact_prompt_and_gold_target():
    rows = training_rows(CONFIGS["b3l"], CASES, catalog=CATALOG, linkings={"q1": LINKING})
    assert rows[0]["target"] == "SELECT 1 AS one"
    assert "APPROVED JOINS" not in rows[0]["messages"][0]["content"]
    with pytest.raises(ValueError):
        training_rows(CONFIGS["b2"], CASES, catalog=CATALOG)
