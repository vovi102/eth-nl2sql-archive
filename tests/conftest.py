from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from eth_nl2sql.store.build import connect, create_schema, load_labels

FIXTURES = Path(__file__).parent / "fixtures"
MINI_DICTIONARY = FIXTURES / "mini_dictionary"
P = "nl2sparql-thesis.nl2sparql_analytics"


def address(n: int) -> str:
    return "0x" + format(n, "040x")


USER = address(0xA11CE)
BINANCE = [address(0xB1), address(0xB2), address(0xB3)]
TORNADO = [address(0x7C1), address(0x7C2)]
UNISWAP = address(0xD1)
TETHER = address(0x7E7)


def ts(day: int, hour: int = 12) -> datetime:
    return datetime(2026, 6, day, hour, tzinfo=UTC)


ETH = 10**18


def tx(tx_hash, sender, recipient, wei, *, day, status=1, index=0, gas_used=21000) -> tuple:
    """One `transactions` row in RAW_SCHEMAS column order."""
    block = day * 100
    return (
        tx_hash,
        index,
        sender,
        recipient,
        Decimal(wei),
        90000,
        10,
        gas_used,
        None,
        status,
        ts(day),
        block,
        f"0xB{block}",
        2,
    )


def make_store():
    """A tiny store: Binance has three addresses, one inflow falls outside the first week."""
    con = connect()
    create_schema(con)
    transactions = [
        tx("0xT1", USER, BINANCE[0], ETH, day=1),
        tx("0xT2", USER, BINANCE[1], 2 * ETH, day=2),
        tx("0xT3", BINANCE[0], USER, ETH // 2, day=3, status=0),
        tx("0xT4", USER, BINANCE[2], 3 * ETH, day=9),
        tx("0xT5", USER, TORNADO[0], ETH // 10, day=4, index=1),
        tx("0xT6", TORNADO[1], UNISWAP, ETH // 10, day=5, index=1, gas_used=80000),
    ]
    con.executemany("INSERT INTO transactions VALUES (" + ", ".join("?" * 14) + ")", transactions)
    con.executemany(
        "INSERT INTO blocks VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(ts(d), d * 100, f"0xB{d}00", USER, 1000 * d, d, 7) for d in (1, 2, 3, 4, 5, 9)],
    )
    con.executemany(
        "INSERT INTO token_transfers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (TETHER, USER, BINANCE[0], "2500000", "0xT1", 0, ts(1), 100, "0xB100"),
            (TETHER, BINANCE[1], USER, "1000000", "0xT2", 1, ts(2), 200, "0xB200"),
        ],
    )
    con.executemany(
        "INSERT INTO contracts VALUES (?, ?, ?, ?, ?, ?)",
        [
            (TETHER, False, False, datetime(2017, 1, 1, tzinfo=UTC), 1, "0xOLD"),
            (TETHER, True, False, datetime(2018, 1, 1, tzinfo=UTC), 2, "0xNEW"),
        ],
    )
    con.execute(
        "INSERT INTO amended_tokens VALUES (?, ?, ?, ?)", (TETHER, "USDT", "Tether USD", "6")
    )
    load_labels(con, MINI_DICTIONARY / "entities.json")
    return con


@pytest.fixture()
def store():
    con = make_store()
    yield con
    con.close()
