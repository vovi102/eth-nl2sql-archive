# T10 — Compact controls and three training seeds

Implemented on 28/10/2026. This is infrastructure validation with offline fixtures and
simulated GPU backends. No LLM experiment was run and benchmark v2 remains draft.

A separate [prompt parity check](prompt-parity.json) also renders all 100 actual
`dev_eval` cases with the existing verified linking cache: both compact control pairs
match inference and supervised messages exactly, with zero mismatches. This check
loads no model and generates no predictions.

`b3-base` and `b3l-base` load the pinned base model without an adapter. Their messages
and per-question prompt hashes exactly equal `b3` and `b3l`, respectively. `RunConfig`
selects `prompt_style` independently of `fine_tuned`. Existing catalog/five-shot variants
remain available. Generation uses the same pinned tokenizer, 4-bit model, greedy settings,
maximum output length, extraction, validator and evaluator for both compact controls and QLoRA.

Training seeds 42/43/44 share the same rendered train/dev inputs and QLoRA settings. The
backend seeds Python, NumPy, torch and CUDA before constructing model/adapter/Trainer;
Trainer receives both `seed` and `data_seed`. Evaluation/save steps are unchanged, with
minimum dev `eval_loss`, best-checkpoint reload and early stopping. Decoding seed 42 and
bootstrap seed 42 are separate from the training seed.

Prepare inputs locally (linking requires the `embed` extra; use one consistent linking
pipeline for train, dev and dev_eval):

```bash
for split in train dev dev_eval; do
  uv run --locked eth-nl2sql link --split "$split"
done
for config in b3 b3l; do
  uv run --locked eth-nl2sql prompts --config "$config" --training
done
for config in b3 b3l b3-base b3l-base; do
  uv run --locked eth-nl2sql prompts --config "$config" --split dev_eval
done
```

On a GPU host with the `gpu` extra and access to the pinned Llama model (or use the
updated Kaggle notebooks):

```bash
eth-nl2sql preflight --config b3 --training --seed all
eth-nl2sql preflight --config b3l --training --seed all
eth-nl2sql train --config all --seed all
# After interruption, continue the matrix; completed verified runs are skipped.
eth-nl2sql train --config all --seed all --resume
for config in b3 b3l; do
  eth-nl2sql generate --config "$config" --seed all
done
for config in b3-base b3l-base; do
  eth-nl2sql generate --config "$config" --seed 42
done
```

Copy `runs/` back intact, then evaluate locally:

```bash
for config in b3 b3l; do
  uv run --locked eth-nl2sql evaluate --config "$config" --seed all
done
for config in b3-base b3l-base; do
  uv run --locked eth-nl2sql evaluate --config "$config"
done
uv run --locked eth-nl2sql report
```

Rendered prompts/SFT inputs are shared at `runs/<config>/`. Outputs live at
`runs/<config>/seed-<seed>/`: `checkpoints/`, `adapter/`, `training-summary.json`,
`training-manifest.json`, `preflight-training.json`, `predictions-dev_eval.jsonl`,
`predictions-dev_eval.manifest.json`, `cases-dev_eval.jsonl`, `eval-dev_eval.json` and
`eval-dev_eval.manifest.json`. Base controls have no training/adapter artifacts. The
explicit `--adapter` option, if used, must select the matching seed's adapter; the default
resolves it automatically. Existing unseeded model predictions are not reused; legacy
unseeded evaluation reports and `gold-echo` remain readable.

Training resume checks model pin, prompt/SFT input hashes, run config, seed, QLoRA settings
and code identity. Checkpoint callbacks save provenance and a checksum of checkpoint files,
including Trainer/optimizer/RNG state; all retained checkpoints are verified before resume
because Trainer can reload an earlier best checkpoint. A completed run also verifies its
adapter and summary. No artifacts may be reused without their manifest. A new seed with
no artifacts starts normally with `--resume`; a stopped run before its first checkpoint can
restart with the same verified identity.

Generator revisions must be immutable commit SHAs; symbolic revisions such as `main`
are rejected before model loading. Generation verifies the full prompt file, per-row
prompt hashes, model pin, generation
settings and adapter contents/own training manifest, even when no rows remain. Predictions
have per-row provenance/content checksums and a final file checksum. Partial `--limit` runs
and interrupted sessions continue without repeating IDs. A session stopped after the
last append can finalize its verified manifest without loading the model again; unavailable
resource measurements are marked explicitly. Do not edit prompt files or
adapters under an existing run; provenance changes require a new run directory/archive.
Checksums describe exact contents and prevent accidental reuse; they are not signatures.

Preflight validates nonempty inputs, unique IDs, message shape, nonempty SQL targets and
train/dev ID separation before loading GPU dependencies. Tokenization uses complete SQL
plus end-of-turn token and never truncates. It records kept/dropped IDs and lengths, prompt,
target, kept and dropped token totals; an empty train **or dev** after filtering is an error.
Generation rejects context overflow and records output `finish_reason` when the token limit
is reached. Resource reports include session runtime, input/output token counts and per-GPU
peak allocated memory, maximum reserved memory and hardware. Peaks reset before model load
for each seed; prior Trainer cycles are collected before the next model is loaded. A failed
Python session records its measured resources; an externally killed process may not be
able to record its last resource measurements.

`report` writes per-seed results and `runs/seed-summary-dev_eval.json`, with mean and sample
standard deviation (ddof=1) for all six scalar evaluation metrics and EX per group. It checks
that seeds share data/IDs, prompts, model, decoding, training protocol, evaluation settings,
store and group sizes. It reports missing seeds and leaves SD null for a single run.
`n_questions` stays N, never 3N; question bootstrap CIs remain per seed. Exact McNemar
comparisons remain paired by question and are reported separately for each training seed,
including compact base versus adapter (a single seed-42 greedy base can be reused).

The default split is still `dev_eval`; explicit `--split test` is gated on frozen benchmark
v2 before prompts, preflight, generation, evaluation or reporting. T10 does not freeze or
run predictions against the authored draft.

Validation commands: `uv run --locked pytest -q --junitxml=reports/experiments-t10/tests.xml`,
`uv run --locked ruff check src tests` and `uv run --locked eth-nl2sql check-sql`.
The SQL check compiled 1,547 gold queries without failures. Notebook JSON and ordinary
Python cells were also parsed locally; the GPU notebook execution remains untested.
Final verification: **312 tests passed**, including **30 T10 tests**; Ruff passed.
The complete test result is saved in [tests.xml](tests.xml).

The T10 suite exercises exact prompt parity, all six distinct output trees, deterministic
seed propagation and production Trainer wiring, full SQL/drop accounting, invalid/empty
inputs, checkpoint/adapter/prompt/model provenance, partial/interrupted generation,
per-seed evaluation/reporting and the draft-test gate. No GPU or model download is used.
