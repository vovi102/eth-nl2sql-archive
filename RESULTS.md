# Results

Split `dev_eval`; execution accuracy (EX) on the local DuckDB replica. Regenerate with `eth-nl2sql report`.

Evaluation role: development; sample execution does not establish full snapshot parity.

| Config | N | EX % (95% CI) | Valid SQL % | Format OK % | EM % | Generic EX % | Entity EX % | Gen p50 s | Gen p95 s |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| b3-base/seed-42 | 100 | 0.0 (0.0–0.0) | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 13.3 | 19.8 |
| b3l-base/seed-42 | 100 | 0.0 (0.0–0.0) | 0.0 | 1.0 | 0.0 | 0.0 | 0.0 | 16.2 | 24.9 |
| gold-echo | 100 | 100.0 (100.0–100.0) | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | – | – |

## EX by blockchain-specific case

| Config | multi_address | alias | class_level | ambiguous_property |
|---|---:|---:|---:|---:|
| b3-base/seed-42 | 0.0 | 0.0 | 0.0 | 0.0 |
| b3l-base/seed-42 | 0.0 | 0.0 | 0.0 | 0.0 |
| gold-echo | 100.0 | 100.0 | 100.0 | 100.0 |

## Paired comparisons (exact McNemar)

| Left | Right | Question | Left only | Right only | p |
|---|---|---|---:|---:|---:|
| b3-base/seed-42 | b3l-base/seed-42 | linking, compact base | 0 | 0 | 1.000 |

## Across training seeds

N is the number of shared questions per seed; seeds are repeated training runs. Mean and sample standard deviation (ddof=1) describe variation across seeds. Question bootstrap CIs remain in the per-seed table above; predictions are never pooled.

| Config | Seeds present | Missing | N questions | EX % mean ± SD | Valid SQL % mean ± SD |
|---|---|---|---:|---|---|
| b3-base | 42 | – | 100 | 0.0 ± – | 0.0 ± – |
| b3l-base | 42 | – | 100 | 0.0 ± – | 0.0 ± – |
