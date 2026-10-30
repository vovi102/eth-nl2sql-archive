# Code maintenance review — 2026-10-30

The reported duplication and coupling were confirmed in the working tree. Smell
names remain design judgments; the seed parsing, missing guards, and notebook
mutation also had observable failure cases.

Two details need qualification: `snapshot.write_json` did not literally shadow
an imported `config.write_json` in the same scope; the shared name obscured their
different atomicity/durability contracts. Also, `report.SPECIFICS` was the subset
of annotation groups excluding `generic`, rather than an exact copy of `GROUPS`.
That subset is preserved. File length alone does not establish Divergent Change
or Feature Envy; the extraction follows the concrete responsibilities identified
in the review.

| Observation | Verification and resulting change |
| --- | --- |
| T11A/T11B duplicate workflow | Both implemented bundles, stage logging, input checks, runtime capture, output archives, and collection. These now live in `src/eth_nl2sql/gpu_workflow.py`. Experiment-specific steps and overwrite policies remain in the scripts. Collection validates the entire archive before writing, and repeated archiving excludes its own manifest. |
| Missing T11B guards | `gpu` now requires `--hf-home` at argument parsing and checks CUDA before reading the mounted model cache. Failed GPU stages still publish status and diagnostic artifacts. |
| Job identifiers | Regression tests reproduced `b3-seed-7 → -7` and `b3-seed-123 → 23` through the actual evaluation entry point. `Job(config, seed)` in `generation/runs.py` now parses the complete seed and validates the identifier. GPU, evaluation, notebook, review, and quota code use this representation. |
| Repeated fine-tuning switches | Training selections use `training_configs()` and adapter/SFT decisions use `RunConfig.fine_tuned`. Explicit names remain where they describe a particular experiment or comparison. |
| Notebook mutation and naming | Two consecutive T11B builds previously produced different source. Both builders now share `gpu_notebook.py` with explicit requirements, job, compression, and logging parameters. T11B writes `t11b.ipynb`, validates generated Python before writing, and retains the source-size check. It does not mutate T11A globals. |
| CLI responsibilities/private helpers | Linking cache/provenance moved to public functions in `linking/workflow.py`; release-checked split reading moved to `data/splits.py`; example-cache validation moved to `generation/retrieval.py`; evaluation and its provenance assembly moved to `evaluation_workflow.py`. Preparation scripts and tests use the public functions. |
| Duplication inside CLI | One output-path guard protects input files and rejects colliding report paths. The live retriever is callable for a case. SQL smoke and dataset compilation share `store/compile.py`. |
| Hash/I/O helpers and constants | `artifacts.py` owns streaming file hashes, UTF-8 text hashes, canonical JSON hashes, and atomic JSON publication. Snapshot journals retain file and directory fsync. Existing import names are compatibility aliases; internal code distinguishes `sha256_file` from `json_digest`. The public dataset constant has one definition, and report groups derive from annotations. |
| Kaggle identity/date literals | Deployment defaults moved to `configs/kaggle.toml`, separate from experimental settings. Builders and continuation use `kaggle.py`. Existing continuation records keep their recorded kernel identifiers. |

## Deployment configuration

Edit `configs/kaggle.toml`, or override individual defaults with
`ETH_NL2SQL_KAGGLE_OWNER`, `ETH_NL2SQL_KAGGLE_RUN_TAG`, and
`ETH_NL2SQL_KAGGLE_ENVIRONMENT_CACHE`. The run tag stays explicit so restarting a
controller on another date does not silently choose a different kernel.

Notebook builders accept `--kernel` and `--cache-kernel`. The T11B controller also
accepts `--owner`, `--run-tag`, and `--pilot-kernel`.

## Compatibility and scope

Canonical hash algorithms and manifest fields are preserved. Source checksums
naturally change when the code changes: old GPU artifacts retain their original
provenance and are not relabeled as outputs from the refactored code. The fixed
experimental training seeds remain 42, 43, and 44; parsing an identifier no longer
assumes that a seed has two digits.

The separate, pre-existing diagnostic notebook builder still imports T11A's
`BOOTSTRAP` and T11B's `LIVE_PROCESS`. Those exports are retained for compatibility;
its notebook construction was smoke checked locally without modifying that script.

No GPU jobs were submitted or rerun, and experiment reports/data/artifacts were
not regenerated. Pre-existing workspace changes were retained.

## Validation

The initial suite passed 337 tests. Before the fixes, the new regression command
`pytest -q tests/test_gpu_workflow.py` reproduced four failures: both seed-width
cases, repeat notebook construction, and the missing CUDA guard.

Post-change tests cover those cases, missing CLI arguments, payload round trips,
archive checksums, collection before any write, output-manifest reuse, stage
failure logs, hash compatibility, and interrupted atomic writes. Existing tests
exercise leakage checks, SQL compilation, benchmark gates, and the full six-run
training/generation/evaluation workflow with fake GPU backends.

Validation commands: `.venv/bin/pytest -q`, `.venv/bin/ruff check src scripts tests`,
and `git diff HEAD --check` for the changed source, tests, and maintenance report.
Real CUDA training and Kaggle execution were not exercised.

Final validation on 2026-10-30: **360 tests passed** in 149.27 seconds; Ruff and
the whitespace check passed. The snapshot crash-recovery test now injects its
interruption through `atomic_write_json` and verifies durable journal publication.
