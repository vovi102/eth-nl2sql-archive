"""Direct linking metrics include missed mentions and align properties by mention."""

from copy import deepcopy

from eth_nl2sql.linking.evaluate import score_predictions


def gold():
    return {
        "id": "q1",
        "schema": {
            "relations": ["transaction_facts"],
            "columns": [
                {"relation": "transaction_facts", "column": "to_address"},
            ],
        },
        "entities": [
            {
                "mention": {"text": "A", "start": 0, "end": 1},
                "owner": "A",
                "addresses": ["0x1", "0x2"],
                "address_scope": "known_owner_addresses",
            },
            {
                "mention": {"text": "B", "start": 5, "end": 6},
                "owner": "B",
                "addresses": ["0x3"],
                "address_scope": "known_owner_addresses",
            },
        ],
        "classes": [
            {
                "mention": {"text": "DEX", "start": 10, "end": 13},
                "category": "dex",
                "concept_class": "DEXProtocol",
                "owners": ["D1", "D2"],
            }
        ],
        "properties": {
            "direction": [
                {"target": "entity:0", "value": "from"},
                {"target": "entity:1", "value": "to"},
            ],
            "fact": "transaction",
            "address_role": [
                {"target": "entity:0", "value": "endpoint"},
            ],
        },
    }


def test_metrics_count_wrong_address_sets_missing_mentions_and_properties():
    annotation = gold()
    prediction = deepcopy(annotation)
    prediction["entities"] = [prediction["entities"][0]]
    prediction["entities"][0]["addresses"] = ["0x1"]
    prediction["properties"]["direction"] = [{"target": "entity:0", "value": None}]
    prediction["classes"][0]["owners"] = ["D1"]
    report = score_predictions([prediction], [annotation])
    metrics = report["metrics"]
    assert metrics["relation_recall@3"] == {"correct": 1, "total": 1, "rate": 1.0}
    assert metrics["entity"] == {"correct": 1, "total": 2, "rate": 0.5}
    assert metrics["address_set"]["correct"] == 0
    assert metrics["class"]["rate"] == 1
    assert metrics["class_membership"]["rate"] == 0
    assert metrics["direction"] == {"correct": 0, "total": 2, "rate": 0.0}
    assert metrics["address_role"]["rate"] == 1
    assert report["evaluation_scope"] == "development"
    assert "draft" in report["notice"].lower()


def test_properties_follow_mentions_even_when_prediction_order_differs():
    annotation = gold()
    prediction = deepcopy(annotation)
    prediction["entities"].reverse()
    prediction["properties"]["direction"] = [
        {"target": "entity:0", "value": "to"},
        {"target": "entity:1", "value": "from"},
    ]
    prediction["properties"]["address_role"][0]["target"] = "entity:1"
    report = score_predictions([prediction], [annotation])
    assert all(m["rate"] == 1 for m in report["metrics"].values() if m["total"])
    missing = score_predictions([], [annotation])
    assert missing["metrics"]["entity"]["total"] == 2
    assert missing["metrics"]["fact"]["rate"] == 0


def test_zero_denominators_and_schema_cutoffs_are_explicit():
    annotation = gold()
    annotation["entities"] = []
    annotation["classes"] = []
    annotation["properties"] = {"fact": None, "direction": [], "address_role": []}
    prediction = deepcopy(annotation)
    prediction["schema"]["relations"] = ["x", "y", "z", "transaction_facts"]
    result = score_predictions([prediction], [annotation])
    assert result["metrics"]["relation_recall@3"]["rate"] == 0
    assert result["metrics"]["fact"] == {"correct": 0, "total": 0, "rate": None}


def test_known_explicit_address_requires_the_literal_even_with_correct_owner():
    annotation = gold()
    annotation["entities"][0]["address_scope"] = "explicit_address"
    annotation["entities"][0]["addresses"] = ["0x1"]
    prediction = deepcopy(annotation)
    prediction["entities"][0]["addresses"] = ["0x2"]
    report = score_predictions([prediction], [annotation])
    assert report["metrics"]["entity"]["correct"] == 1
    assert report["metrics"]["direction"]["correct"] == 1


def test_single_address_owner_set_can_be_correct_in_representative_baseline():
    annotation = gold()
    prediction = deepcopy(annotation)
    prediction["entities"][0]["addresses"] = ["0x1"]
    for entity in prediction["entities"]:
        entity["address_scope"] = "representative_address"
    report = score_predictions([prediction], [annotation])
    assert report["metrics"]["address_set"] == {"correct": 1, "total": 2, "rate": 0.5}
    assert report["metrics"]["multi_address_set"] == {"correct": 0, "total": 1, "rate": 0.0}
