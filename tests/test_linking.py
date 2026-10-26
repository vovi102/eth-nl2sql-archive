import json

import pytest
from conftest import BINANCE, MINI_DICTIONARY, TORNADO

from eth_nl2sql.config import CATALOG_PATH, SYNONYMS_PATH
from eth_nl2sql.linking.context import Linking, LinkingPipeline, render
from eth_nl2sql.linking.dictionary import load_dictionary
from eth_nl2sql.linking.entity import EntityLinker
from eth_nl2sql.linking.resolver import direction_of
from eth_nl2sql.linking.schema import SchemaLinker


@pytest.fixture(scope="module")
def pipeline():
    dictionary = load_dictionary(MINI_DICTIONARY)
    schema = SchemaLinker(
        json.loads(CATALOG_PATH.read_text()), json.loads(SYNONYMS_PATH.read_text())
    )
    return LinkingPipeline(dictionary, schema, EntityLinker(dictionary))


def entities(pipeline, question):
    return pipeline.link(question).entities


def test_multi_address_owner_carries_all_addresses(pipeline):
    (binance,) = entities(pipeline, "How much ETH did Binance receive in June 2026?")
    assert (binance.kind, binance.name) == ("instance", "Binance")
    assert binance.addresses == tuple(sorted(BINANCE))


@pytest.mark.parametrize("mention", ["TC", "the mixer", "Tornado"])
def test_aliases_resolve_to_the_owner(pipeline, mention):
    (resolved,) = entities(pipeline, f"How many transfers went to {mention} last week?")
    assert (resolved.kind, resolved.name, resolved.direction) == ("instance", "Tornado Cash", "to")
    assert resolved.addresses == tuple(sorted(TORNADO))


def test_typo_is_matched_by_fuzzy_stage(pipeline):
    (resolved,) = entities(pipeline, "Transactions sent by Binnance in June 2026")
    assert (resolved.name, resolved.direction) == ("Binance", "from")


@pytest.mark.parametrize(
    ("question", "concept_class"),
    [
        ("Total value sent to any major DEX in June 2026", "DEXProtocol"),
        ("Which exchanges received the most ETH?", "ExchangeAccount"),
    ],
)
def test_class_level_mentions_resolve_to_concepts(pipeline, question, concept_class):
    (resolved,) = entities(pipeline, question)
    assert (resolved.kind, resolved.concept_class) == ("class", concept_class)


def test_lowercase_common_word_does_not_link_to_a_token(pipeline):
    assert entities(pipeline, "Did bob send anything?") == ()
    (bob,) = entities(pipeline, "How many BOB transfers happened?")
    assert bob.is_token


def test_raw_addresses_are_kept():
    dictionary = load_dictionary(MINI_DICTIONARY)
    unknown = "0x" + "ab" * 20
    (match,) = EntityLinker(dictionary).link(f"List transactions from {unknown}")
    assert match.target_id == f"address:{unknown}"
    (known,) = EntityLinker(dictionary).link(f"List transactions from {BINANCE[1]}")
    assert known.target_id == "owner:Binance"


@pytest.mark.parametrize(
    ("question", "direction"),
    [
        ("ETH sent from Binance", "from"),
        ("ETH received by Binance", "to"),
        ("flows between Binance and Kraken", "unspecified"),
        ("transfers from and to Binance", "unspecified"),
        ("from Tornado Cash to Binance", "to"),
    ],
)
def test_direction_cues(question, direction):
    assert direction_of(question, question.rindex("Binance")) == direction


def test_render_and_round_trip(pipeline):
    linking = pipeline.link("How much ETH did Binance send to the mixer?")
    text = render(linking)
    assert "entity_labels_v1.owner = 'Binance'" in text
    assert "entity_labels_v1.owner = 'Tornado Cash'" in text
    assert Linking.from_json(linking.to_json()) == linking
