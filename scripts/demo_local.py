"""Demo existing CPU components: linking, prompts, validation and gold SQL execution.

Run from the repository root with `.venv/bin/python scripts/demo_local.py`.
This reads the development dataset and opens DuckDB read-only. It does not
call an LLM: the executed SQL comes from the dataset's gold field.
"""

from __future__ import annotations

import argparse
import json

from eth_nl2sql import config as cfg
from eth_nl2sql.generation.runs import CONFIGS, prompt_rows
from eth_nl2sql.linking.context import LinkingPipeline, render
from eth_nl2sql.linking.dictionary import load_dictionary
from eth_nl2sql.linking.entity import EntityLinker
from eth_nl2sql.linking.schema import SchemaLinker
from eth_nl2sql.store.build import connect
from eth_nl2sql.store.execute import QueryResult, execute, to_duckdb
from eth_nl2sql.store.manifest import store_profile
from eth_nl2sql.validation import ValidationError, validate_sql

DEMO_CASES = {
    "t05-e001": "Nhiều địa chỉ của Binance",
    "t05-e035": "Alias TC / Tornado Cash",
    "t05-e039": "Thống kê theo lớp sàn giao dịch",
    "t05-e045": "Binance → SwissBorg: outer transactions",
    "t05-e046": "Binance → SwissBorg: token-transfer events",
}


def print_table(result: QueryResult) -> None:
    rows = [[str(value) for value in row] for row in result.rows[:5]]
    lines = [list(result.columns), *rows]
    widths = [max(len(line[i]) for line in lines) for i in range(len(result.columns))]
    for index, line in enumerate(lines):
        print(" | ".join(value.ljust(width) for value, width in zip(line, widths, strict=True)))
        if index == 0:
            print("-+-".join("-" * width for width in widths))
    print(f"{len(result.rows)} dòng; thời gian chạy SQL: {result.elapsed_ms:.1f} ms")
    if len(result.rows) > 5:
        print("Hiển thị 5 dòng đầu.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--case", choices=DEMO_CASES, action="append", help="Chọn ca; có thể lặp lại tùy chọn."
    )
    parser.add_argument("--show-prompt", action="store_true", help="In đầy đủ prompt B1L.")
    args = parser.parse_args()
    if not cfg.STORE_PATH.is_file():
        parser.error(f"Không tìm thấy DuckDB local: {cfg.STORE_PATH}")

    dataset = cfg.DATA_DIR / "dev_eval.jsonl"
    if not dataset.is_file():
        parser.error(f"Không tìm thấy dataset phát triển: {dataset}")
    cases = {case["id"]: case for case in cfg.read_jsonl(dataset)}
    selected = args.case or list(DEMO_CASES)
    missing = [case_id for case_id in selected if case_id not in cases]
    if missing:
        parser.error(f"Dataset thiếu ca demo: {', '.join(missing)}")

    dictionary = load_dictionary(cfg.DICTIONARY_DIR)
    catalog = json.loads(cfg.CATALOG_PATH.read_text())
    synonyms = json.loads(cfg.SYNONYMS_PATH.read_text())
    pipeline = LinkingPipeline(
        dictionary, SchemaLinker(catalog, synonyms), EntityLinker(dictionary)
    )

    print("DEMO LOCAL — CÁC THÀNH PHẦN ĐÃ CÓ")
    print(f"Dictionary đã kiểm tra: {len(dictionary.address_targets):,} địa chỉ.")
    print("Linking dùng lexical/fuzzy; gợi ý có thể thiếu hoặc nhầm.")
    print("SQL thực thi là SQL chuẩn có sẵn (gold); demo này chưa gọi LLM.")
    with connect(cfg.STORE_PATH) as con:
        profile = store_profile(con)
        print(f"Store: {cfg.STORE_PATH} (read-only)")
        print(f"Scope: {profile['scope']}; complete_snapshot={profile['complete_snapshot']}")
        print(f"Cửa sổ dữ liệu UTC: {profile.get('window')}")

        for index, case_id in enumerate(selected, start=1):
            case = cases[case_id]
            print(f"\n{'=' * 72}\n{index}. {DEMO_CASES[case_id]} [{case_id}]")
            print(f"\nCâu hỏi:\n{case['question']}")
            linking = pipeline.link(case["question"])
            print(f"\nGợi ý linking:\n{render(linking)}")
            prompt = prompt_rows(
                CONFIGS["b1l"], [case], catalog=catalog, linkings={case_id: linking}
            )[0]
            print(f"\nĐã dựng prompt B1L: {len(prompt['messages'])} messages.")
            if args.show_prompt:
                print(json.dumps(prompt["messages"], ensure_ascii=False, indent=2))

            print(f"\nSQL chuẩn từ dataset:\n{case['sql']}")
            validate_sql(case["sql"])
            duck_sql, _ = to_duckdb(case["sql"])
            print(f"\nValidator: PASS\nSQL sau chuyển sang DuckDB:\n{duck_sql}")
            result = execute(con, case["sql"])
            print("\nKết quả thực thi:")
            print_table(result)

    print(f"\n{'=' * 72}\nVí dụ validator từ chối lệnh ghi dữ liệu:")
    rejected_sql = "DROP TABLE `nl2sparql-thesis.nl2sparql_analytics.entity_labels_v1`"
    print(rejected_sql)
    try:
        validate_sql(rejected_sql)
    except ValidationError as exc:
        print(f"ĐÃ CHẶN [{exc.code}]: {exc} (chỉ kiểm tra, không thực thi)")
    else:
        raise RuntimeError("Validator không từ chối lệnh ghi dữ liệu")


if __name__ == "__main__":
    main()
