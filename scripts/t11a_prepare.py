"""Build all T11A linking/prompt/SFT inputs with one pinned encoder runtime."""

import argparse
import importlib.metadata
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from eth_nl2sql import cli  # noqa: E402
from eth_nl2sql import config as cfg  # noqa: E402
from eth_nl2sql.data.splits import read_checked_split  # noqa: E402
from eth_nl2sql.generation.retrieval import load_encoder  # noqa: E402
from eth_nl2sql.generation.runs import training_configs  # noqa: E402
from eth_nl2sql.linking.context import LinkingPipeline, link_rows  # noqa: E402
from eth_nl2sql.linking.dictionary import load_dictionary  # noqa: E402
from eth_nl2sql.linking.entity import EntityLinker  # noqa: E402
from eth_nl2sql.linking.schema import SchemaLinker  # noqa: E402
from eth_nl2sql.linking.workflow import linking_provenance, save_linkings  # noqa: E402


def prepare(device: str) -> None:
    report = ROOT / "reports/experiments/base-controls/linking-runtime.json"
    start = time.monotonic()
    encoder = load_encoder(cfg.load())
    encoder.to(device)
    dictionary = load_dictionary(cfg.DICTIONARY_DIR)
    runtime = {
        "encoder_device": device,
        "packages": {
            name: importlib.metadata.version(name)
            for name in (
                "torch",
                "sentence-transformers",
                "transformers",
                "numpy",
                "rapidfuzz",
            )
        },
    }
    pipeline = LinkingPipeline(
        dictionary,
        SchemaLinker(
            json.loads(cfg.CATALOG_PATH.read_text()),
            json.loads(cfg.SYNONYMS_PATH.read_text()),
            encoder,
        ),
        EntityLinker(dictionary, encoder),
    )
    provenance = {**linking_provenance(cfg.DICTIONARY_DIR, True), "runtime": runtime}
    stages = {"initialization_s": time.monotonic() - start}
    print(json.dumps({"initialization_s": stages["initialization_s"], **runtime}), flush=True)
    for split in ("train", "dev", "dev_eval"):
        started = time.monotonic()
        cases = read_checked_split(split)
        rows = []
        for offset in range(0, len(cases), 100):
            rows.extend(link_rows(pipeline, cases[offset : offset + 100]))
            print(f"{split}: {len(rows)}/{len(cases)}", flush=True)
        save_linkings(split, "full", rows, provenance)
        stages[split] = {"rows": len(rows), "runtime_s": time.monotonic() - started}
        cfg.write_json(report, {"runtime": runtime, "stages": stages})
    for name in training_configs():
        cli.main(["prompts", "--config", name, "--training"])
    for name in (*training_configs(), "b3-base", "b3l-base"):
        cli.main(["prompts", "--config", name, "--split", "dev_eval"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu")
    args = parser.parse_args()
    prepare(args.device)
