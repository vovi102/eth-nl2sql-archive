"""Hash compatibility and interrupted journal publication."""

import hashlib
import json

import pytest

from eth_nl2sql.artifacts import atomic_write_json, json_digest, sha256_file, text_digest


def test_hashes_preserve_existing_file_text_and_canonical_json_identities(tmp_path):
    text = "Câu hỏi Ethereum\n"
    path = tmp_path / "input.txt"
    path.write_text(text)
    expected = hashlib.sha256(text.encode()).hexdigest()
    assert sha256_file(path) == text_digest(text) == expected
    value = {"z": [text], "a": 42}
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert json_digest(value) == hashlib.sha256(canonical.encode()).hexdigest()
    assert json_digest(value) == json_digest({"a": 42, "z": [text]})


@pytest.mark.parametrize("durable", [False, True])
def test_atomic_json_failure_keeps_previous_journal_and_removes_temporary(tmp_path, durable):
    path = tmp_path / "journal.json"
    atomic_write_json(path, {"state": "submitted"}, durable=durable)
    with pytest.raises(TypeError):
        atomic_write_json(path, {"invalid": object()}, durable=durable)
    assert json.loads(path.read_text()) == {"state": "submitted"}
    assert list(tmp_path.iterdir()) == [path]
