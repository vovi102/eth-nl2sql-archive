import copy
import json
import shutil
from datetime import UTC, datetime

import pytest
from conftest import BINANCE, MINI_DICTIONARY, TETHER, USER, tx

from eth_nl2sql.cli import main
from eth_nl2sql.config import DATA_DIR, DICTIONARY_DIR, sha256_file, write_json
from eth_nl2sql.linking.audit import check_dictionary, dictionary_coverage, render_coverage
from eth_nl2sql.linking.dictionary import load_dictionary, normalize_phrase
from eth_nl2sql.linking.entity import EntityLinker
from eth_nl2sql.linking.resolver import Resolver
from eth_nl2sql.linking.validation import read_dictionary, validate_graph
from eth_nl2sql.store.build import connect, create_schema, load_labels


@pytest.fixture(scope="module")
def v2():
    return load_dictionary(DICTIONARY_DIR)


def strict_fixture():
    rows, aliases, concepts = read_dictionary(MINI_DICTIONARY)
    for row in rows:
        row["aliases"] += [normalize_phrase(row["owner"])]
    for phrase, owner in aliases.items():
        for row in rows:
            if row["owner"] == owner:
                row["aliases"].append(phrase)
    aliases = {alias: row["owner"] for row in rows for alias in row["aliases"]}
    concepts["token_contract"] = {
        "aliases": ["token contract"], "description": "Tokens.",
        "ontology_class": "https://example.org/TokenContract", "instances": ["Tether", "BOB"],
    }
    return rows, aliases, concepts


def test_real_v2_loads_preserves_v1_addresses_and_has_verified_multi_address_owners(v2):
    v1 = load_dictionary(DATA_DIR / "entities" / "v1")
    assert set(v1.address_targets) <= set(v2.address_targets)
    stats = check_dictionary(DICTIONARY_DIR)
    assert 40 <= stats["operational_owners"] <= 60
    assert stats["multi_address_operational_owners"] >= 40
    assert set(stats["categories"]) >= {"dex", "exchange", "mixer"}
    # Metadata must be accepted by SQL ingestion, not just the lexical loader.
    with connect() as con:
        create_schema(con)
        assert load_labels(con, DICTIONARY_DIR / "entities.json") == stats["addresses"]
        assert con.execute(
            "SELECT count(DISTINCT address) FROM entity_labels_v1 WHERE owner='Tornado Cash'"
        ).fetchone()[0] == 20
        assert con.execute(
            "SELECT DISTINCT category, concept_class FROM entity_labels_v1 "
            "WHERE owner='Tornado Cash'"
        ).fetchall() == [("mixer", "MixerAccount")]


@pytest.mark.parametrize("mention", ["TC", "the mixer", "Tornado Cash", "tornado"])
def test_real_mixer_aliases_expand_to_operational_contracts(v2, mention):
    question = f"to {mention}"
    (resolved,) = Resolver(v2).resolve(question, EntityLinker(v2).link(question))
    assert (resolved.name, resolved.is_token, resolved.direction) == ("Tornado Cash", False, "to")
    assert len(resolved.addresses) >= 4
    assert "0x77777feddddffc19ff86db637967013e6c6a116c" not in resolved.addresses


@pytest.mark.parametrize("mention,owner", [
    ("TORN", "Tornado Cash Token"), ("CET", "CoinEx Token"), ("BORG", "SwissBorg Token"),
])
def test_governance_tokens_remain_separate_from_operations(v2, mention, owner):
    (resolved,) = Resolver(v2).resolve(mention, EntityLinker(v2).link(mention))
    assert resolved.name == owner and resolved.is_token


@pytest.mark.parametrize("question,klass", [
    ("to any major DEX", "DEXProtocol"), ("to exchanges", "ExchangeAccount"),
    ("to mixers", "MixerAccount"),
])
def test_real_group_mentions_resolve_to_class(v2, question, klass):
    (resolved,) = Resolver(v2).resolve(question, EntityLinker(v2).link(question))
    assert (resolved.kind, resolved.concept_class) == ("class", klass)
    assert v2.owners_of_class(klass)


def test_shared_protocol_alias_is_explicitly_ambiguous(v2):
    (resolved,) = Resolver(v2).resolve("Uniswap", EntityLinker(v2).link("Uniswap"))
    assert resolved.kind == "ambiguous"
    assert set(resolved.candidates) == {"Uniswap V2", "Uniswap V3", "Uniswap V4"}


def test_renamed_token_aliases_agree_with_retained_local_metadata(v2):
    evidence = json.loads((DICTIONARY_DIR / "evidence" / "token-metadata.json").read_text())
    assert len(evidence["rows"]) == 19
    for row in evidence["rows"]:
        target = v2.by_id[v2.address_targets[row["address"]]]
        assert target.is_token_owner
        assert normalize_phrase(row["symbol"]) in target.aliases


@pytest.mark.parametrize("damage,error", [
    ("duplicate", "duplicate label address"), ("address", "invalid Ethereum address"),
    ("chain", "chain_id"), ("lower", "address_lower"), ("sources", "sources"),
    ("date", "ISO date"), ("source_date", "retrieved after"),
    ("alias", "unknown owner"), ("normalized_alias", "conflicting normalized alias"),
    ("instances", "instances differ"), ("class", "inconsistent owner category/class"),
    ("role", "role mismatch"), ("row_alias", "alias map differs"),
])
def test_invalid_graph_is_rejected(damage, error):
    rows, aliases, concepts = strict_fixture()
    if damage == "duplicate":
        rows.append({**rows[0], "address": rows[0]["address"].upper().replace("0X", "0x")})
    elif damage == "address":
        rows[0]["address"] = "0xabc"
    elif damage == "chain":
        rows[0]["chain_id"] = 10
    elif damage == "lower":
        rows[0]["address_lower"] = USER
    elif damage == "sources":
        rows[0]["sources"] = []
    elif damage == "date":
        rows[0]["verified_date"] = "20261026"
    elif damage == "source_date":
        rows[0]["sources"][0]["retrieved_date"] = "2026-10-27"
    elif damage == "alias":
        aliases["lost"] = "unknown"
    elif damage == "normalized_alias":
        aliases["BINANCE "] = "Tether"
    elif damage == "instances":
        concepts["exchange"]["instances"] = []
    elif damage == "class":
        rows[0]["concept_class"] = "Mixer"
    elif damage == "role":
        rows[0]["address_role"] = "token"
    elif damage == "row_alias":
        rows[0]["aliases"].append("unlisted")
    with pytest.raises(ValueError, match=error):
        validate_graph(rows, aliases, concepts, strict=True)


def test_manifest_detects_modified_dictionary(tmp_path):
    for name in ("entities.json", "aliases.json", "concepts.json", "manifest.json"):
        shutil.copyfile(DICTIONARY_DIR / name, tmp_path / name)
    with (tmp_path / "aliases.json").open("a") as handle:
        handle.write("\n")
    with pytest.raises(ValueError, match="checksum mismatch: aliases.json"):
        load_dictionary(tmp_path)


def test_valid_graph_and_explicit_shared_alias_are_accepted():
    rows, aliases, concepts = strict_fixture()
    aliases["shared platform"] = ["Binance", "Uniswap V3"]
    for row in rows:
        if row["owner"] in aliases["shared platform"]:
            row["aliases"].append("shared platform")
    validate_graph(rows, aliases, concepts, strict=True)


def test_manifest_detects_modified_source_evidence(tmp_path):
    shutil.copytree(DICTIONARY_DIR, tmp_path / "v2")
    snapshot = tmp_path / "v2" / "evidence" / "binance-por.json"
    snapshot.write_text("{}\n")
    with pytest.raises(ValueError, match="source snapshot checksum mismatch"):
        load_dictionary(tmp_path / "v2")


def test_coverage_counts_events_once_per_owner_and_keeps_zero_activity(store):
    # Two different Binance addresses and a self-transfer exercise both kinds
    # of duplication. Out-of-window activity must not increase counts.
    store.execute("INSERT INTO transactions VALUES (" + ", ".join("?" * 14) + ")",
                  tx("internal", BINANCE[0], BINANCE[1], 1, day=6))
    store.execute("INSERT INTO transactions VALUES (" + ", ".join("?" * 14) + ")",
                  tx("self", BINANCE[0], BINANCE[0], 1, day=7))
    outside = list(tx("outside", BINANCE[0], USER, 1, day=1))
    outside[10] = datetime(2026, 7, 1, tzinfo=UTC)
    store.execute("INSERT INTO transactions VALUES (" + ", ".join("?" * 14) + ")", outside)
    report = dictionary_coverage(store, MINI_DICTIONARY)
    owners = {r["owner"]: r for r in report["owners"]}
    addresses = {r["address"]: r for r in report["addresses"]}
    assert owners["Binance"]["transactions_any"] == 6
    assert owners["Binance"]["transactions_from"] == 3
    assert owners["Binance"]["transactions_to"] == 5
    assert addresses[BINANCE[0]]["transactions_any"] == 4
    assert addresses[TETHER]["transactions_any"] == 0
    assert addresses[TETHER]["token_transfers_token"] == 2
    assert addresses[TETHER]["contracts"] == 2
    assert addresses[TETHER]["token_metadata"] == 1
    assert owners["BOB"]["active_addresses"] == 0
    assert report["tables"]["transactions"] == {
        "rows": 8, "matched_rows": 8, "matched_fraction": 1.0,
    }
    assert report["tables"]["token_transfers"]["matched_rows"] == 2
    assert sum(o["token_transfers_any"] for o in owners.values()) > 2
    assert "coverage toàn mạng" in render_coverage(report)


def test_empty_store_coverage_retains_all_labels_and_null_rates():
    with connect() as con:
        create_schema(con)
        report = dictionary_coverage(con, MINI_DICTIONARY)
    assert report["summary"]["active_addresses"] == 0
    assert report["tables"]["transactions"]["matched_fraction"] is None
    assert len(report["addresses"]) == check_dictionary(MINI_DICTIONARY)["addresses"]


def test_coverage_uses_measured_dictionary_without_changing_loaded_labels(store, tmp_path):
    rows, aliases, concepts = read_dictionary(MINI_DICTIONARY)
    rows = copy.deepcopy(rows)
    for row in rows:
        if row["owner"] == "Binance":
            row["owner"] = "Renamed Exchange"
    aliases = {a: "Renamed Exchange" if o == "Binance" else o for a, o in aliases.items()}
    concepts["exchange"]["instances"] = ["Renamed Exchange"]
    for name, values in (("entities", rows), ("aliases", aliases), ("concepts", concepts)):
        write_json(tmp_path / f"{name}.json", values)
    report = dictionary_coverage(store, tmp_path)
    assert next(o for o in report["owners"] if o["owner"] == "Renamed Exchange")[
        "transactions_any"
    ] == 4
    assert store.execute(
        "SELECT DISTINCT owner FROM entity_labels_v1 WHERE address=?", [BINANCE[0]]
    ).fetchone() == ("Binance",)


def test_cli_defaults_to_v2(capsys):
    main(["check-dictionary"])
    report = json.loads(capsys.readouterr().out)
    assert report["files"]["entities.json"] == sha256_file(DICTIONARY_DIR / "entities.json")


def test_coverage_cli_protects_input_paths():
    with pytest.raises(SystemExit, match="must not overwrite"):
        main(["dictionary-coverage", "--out", str(DICTIONARY_DIR / "entities.json")])
