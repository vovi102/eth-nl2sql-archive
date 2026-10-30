"""Audit actual original train/dev label spans; no model weights or test data."""

import importlib.metadata
import os

from eth_nl2sql import config as cfg
from eth_nl2sql.generation.backend import load_tokenizer, stop_token_ids
from eth_nl2sql.train_qlora import PaddingCollator, encode_row

os.environ.update(
    HF_HOME=str(cfg.ROOT / ".cache/kaggle-model/hf-home"),
    HF_HUB_OFFLINE="1",
    TRANSFORMERS_OFFLINE="1",
)
tokenizer = load_tokenizer(cfg.load())
tokenizer.pad_token = tokenizer.pad_token or tokenizer.eos_token
report = {"scope": "original b3 SFT train/dev, all rows", "splits": {}}
shortest = longest = None
for split in ("train", "dev"):
    path = cfg.ROOT / f"runs/b3/sft-{split}.jsonl"
    rows = cfg.read_jsonl(path)
    prompt_count = target_count = 0
    for row in rows:
        prompt = tokenizer.apply_chat_template(row["messages"], add_generation_prompt=True)
        target = tokenizer(row["target"], add_special_tokens=False)["input_ids"]
        target += [stop_token_ids(tokenizer)[-1]]
        feature = encode_row(tokenizer, row, cfg.load()["qlora"]["max_length"])
        assert feature is not None, row["id"]
        assert feature["input_ids"] == prompt + target, row["id"]
        assert feature["labels"][: len(prompt)] == [-100] * len(prompt), row["id"]
        assert feature["labels"][len(prompt) :] == target, row["id"]
        assert len(target) > 1 and all(t != -100 for t in target), row["id"]
        prompt_count += len(prompt)
        target_count += len(target)
        if shortest is None or len(feature["input_ids"]) < len(shortest["input_ids"]):
            shortest = feature
        if longest is None or len(feature["input_ids"]) > len(longest["input_ids"]):
            longest = feature
    report["splits"][split] = {
        "rows_checked": len(rows),
        "source_sha256": cfg.sha256_file(path),
        "masked_prompt_tokens": prompt_count,
        "sql_eot_tokens": target_count,
        "missing_or_truncated_targets": 0,
        "incorrect_label_spans": 0,
    }
batch = PaddingCollator(tokenizer.pad_token_id)([shortest, longest])
report["padding_labels_masked"] = bool(
    (batch["labels"][batch["attention_mask"] == 0] == -100).all()
)
assert report["padding_labels_masked"]
report["versions"] = {
    m: importlib.metadata.version(m) for m in ("transformers", "tokenizers", "torch")
}
report["note"] = "Local tokenizer/span audit; pinned GPU loss arithmetic is checked separately."
cfg.write_json(cfg.ROOT / "reports/experiments/diagnosis/masking-all-rows.json", report)
print(report)
