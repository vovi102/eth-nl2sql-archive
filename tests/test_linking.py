import json
from dataclasses import replace

import numpy as np
import pytest
from conftest import BINANCE, MINI_DICTIONARY, TORNADO

from eth_nl2sql.config import CATALOG_PATH, SYNONYMS_PATH
from eth_nl2sql.linking.context import Linking, LinkingPipeline, link_rows, render
from eth_nl2sql.linking.dictionary import load_dictionary
from eth_nl2sql.linking.entity import EntityLinker
from eth_nl2sql.linking.resolver import direction_of
from eth_nl2sql.linking.schema import SchemaLinker
from eth_nl2sql.linking.variants import VARIANTS


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
        ("flows between Binance and Kraken", "either"),
        ("transfers from and to Binance", "either"),
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


def test_prediction_uses_t07_mentions_and_preserves_explicit_address_scope(pipeline):
    question = f"Transactions from {BINANCE[1]} to Binance"
    linking = pipeline.link(question)
    result = linking.to_json()
    assert result["schema_version"] == 2
    assert result["entities"][0]["mention"] == {
        "text": BINANCE[1],
        "start": 18,
        "end": 60,
    }
    assert result["entities"][0]["owner"] == "Binance"
    assert result["entities"][0]["addresses"] == [BINANCE[1]]
    assert result["entities"][0]["address_scope"] == "explicit_address"
    assert result["entities"][1]["addresses"] == sorted(BINANCE)
    assert result["properties"]["direction"] == [
        {"target": "entity:0", "value": "from"},
        {"target": "entity:1", "value": "to"},
    ]
    assert Linking.from_json(result) == linking


@pytest.mark.parametrize(
    "question,direction,fact,role",
    [
        ("How much ETH did Binance send?", "from", "transaction", "endpoint"),
        ("How much ETH did Binance receive?", "to", "transaction", "endpoint"),
        ("Transactions involving Binance", "either", "transaction", "endpoint"),
        ("Transactions from and to Binance", "either", "transaction", "endpoint"),
        ("Transactions from Binance", "from", "transaction", "endpoint"),
        ("Token transfer events from Binance", "from", "token_transfer", "endpoint"),
        (
            "Join transactions with token transfer events from Binance",
            "from",
            "transaction_token_transfer_join",
            "endpoint",
        ),
        ("USDT token transfer events", "unspecified", "token_transfer", "token_contract"),
        ("Token transfer events sent to USDT", "to", "token_transfer", "endpoint"),
        ("Transactions sent to USDT", "to", "transaction", "endpoint"),
        ("Token-transfer log events with Binance as sender", "from", "token_transfer", "endpoint"),
        ("Transfer-log events with Binance as recipient", "to", "token_transfer", "endpoint"),
        ("Transactions touching Binance on either endpoint", "either", "transaction", "endpoint"),
        ("USDT", "unspecified", None, None),
        ("Binance", "unspecified", None, None),
    ],
)
def test_property_resolution_requires_question_evidence(pipeline, question, direction, fact, role):
    linking = pipeline.link(question)
    (entity,) = linking.entities
    assert (entity.direction, linking.fact, entity.address_role) == (direction, fact, role)


def test_property_rendering_explains_endpoint_and_unresolved_roles(pipeline):
    endpoint = render(pipeline.link("Token transfer events to USDT"))
    assert "to_address" in endpoint and "endpoint" in endpoint
    assert "token contract Tether" not in endpoint
    assert "unresolved" in render(pipeline.link("USDT"))


def test_ablation_changes_only_its_linking_mechanism(pipeline):
    question = "Token transfer events from BNB exchange to exchanges"
    outputs = {
        name: LinkingPipeline(
            pipeline.entity.dictionary, pipeline.schema, pipeline.entity, variant=name
        ).link(question)
        for name in VARIANTS
    }
    full = outputs["full"]
    for result in outputs.values():
        assert (result.relations, result.fields) == (full.relations, full.fields)
        assert Linking.from_json(result.to_json()) == result
    single = outputs["no_multi_address"]
    assert single.entities[0].addresses == (BINANCE[0],)
    assert single.entities[1:] == full.entities[1:]
    assert single.fact == full.fact
    assert "entity_labels_v1.owner =" not in render(single)
    assert BINANCE[0] in render(single)
    assert all(e.kind == "class" for e in outputs["no_alias"].entities)
    assert outputs["no_alias"].entities[-1] == full.entities[-1]
    assert outputs["no_class"].entities == full.entities[:1]
    no_property = outputs["no_property"]
    assert no_property.fact is None
    assert no_property.entities[0].addresses == full.entities[0].addresses
    assert all(
        e.direction == "unspecified" and e.address_role is None for e in no_property.entities
    )
    assert "from_address" not in render(no_property).split("likely columns:")[1].split("\n", 1)[1]
    baseline = outputs["baseline"]
    assert len(baseline.entities) == 1
    assert baseline.entities[0].addresses == (BINANCE[0],)
    assert baseline.fact is None


def test_baseline_is_exact_only_but_full_keeps_fuzzy_matching(pipeline):
    baseline = LinkingPipeline(
        pipeline.entity.dictionary, pipeline.schema, pipeline.entity, variant="baseline"
    )
    assert baseline.link("Transactions from Binnance").entities == ()
    assert pipeline.link("Transactions from Binnance").entities[0].name == "Binance"


def test_prediction_boundary_never_reads_gold_fields(pipeline):
    class QuestionOnly(dict):
        def __getitem__(self, key):
            assert key in {"id", "question"}, f"Prediction read forbidden field {key}"
            return super().__getitem__(key)

    cases = [
        QuestionOnly(id="q", question="Transactions to Binance", sql=object(), annotation=object())
    ]
    first = link_rows(pipeline, cases)
    assert link_rows(pipeline, cases) == first
    assert "sql" not in first[0] and "annotation" not in first[0]


def test_ambiguous_alias_remains_unresolved_in_normalized_output(pipeline):
    dictionary = pipeline.entity.dictionary
    dictionary = replace(
        dictionary,
        phrases={
            **dictionary.phrases,
            "shared": ("owner:Binance", "owner:Tether"),
        },
    )
    result = (
        LinkingPipeline(dictionary, pipeline.schema, EntityLinker(dictionary))
        .link("Transactions to shared")
        .to_json()
    )
    (entity,) = result["entities"]
    assert entity["status"] == "unresolved" and entity["owner"] is None
    assert entity["addresses"] == []
    assert entity["candidates"] == ["Binance", "Tether"]
    assert result["properties"]["address_role"] == [{"target": "entity:0", "value": None}]


def test_class_then_multiple_explicit_addresses_keep_their_property_targets(pipeline):
    question = f"Transactions from exchanges to {BINANCE[1]} and {BINANCE[2]}"
    linking = pipeline.link(question)
    result = linking.to_json()
    assert result["classes"][0]["owners"] == ["Binance"]
    assert [e["addresses"] for e in result["entities"]] == [[BINANCE[1]], [BINANCE[2]]]
    assert result["properties"]["direction"] == [
        {"target": "class:0", "value": "from"},
        {"target": "entity:0", "value": "to"},
        {"target": "entity:1", "value": "to"},
    ]
    assert Linking.from_json(result) == linking


def test_no_alias_cannot_recover_an_alias_through_embedding_fallback(pipeline):
    class Encoder:
        def encode(self, texts, **kwargs):
            return np.array(
                [
                    [1.0, 0.0]
                    if text.startswith("Owner: Binance")
                    or not text.startswith(("Owner:", "Concept:"))
                    else [0.0, 1.0]
                    for text in texts
                ]
            )

    dictionary = pipeline.entity.dictionary
    no_alias = LinkingPipeline(
        dictionary, pipeline.schema, EntityLinker(dictionary, Encoder()), variant="no_alias"
    )
    assert not any(e.kind == "instance" for e in no_alias.link("BNB exchange").entities)
    assert no_alias.link("Binance").entities[0].name == "Binance"
