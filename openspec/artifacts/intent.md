# Intent: feature-store-lite

## Measurable Claim

One local-first Docker command proves point-in-time correct historical retrieval, zero future leakage, TTL behavior, deterministic Parquet-to-SQLite materialization, exact online values, and warmed Feast SDK p95 latency.

## Problem

Supplies #21 with reproducible, point-in-time correct training features and a local online retrieval contract while #26 protects source quality and #22 observes model behavior.

## In Scope

- Use the selected component pack: `mlops-data-platform`.
- Keep the project under the MLOps and Data Platform program.
- Preserve the benchmark contract: `online_read_latency_p95_ms` in `benchmarks/results/summary.json`.
- Keep the default path local-first and reproducible.

## Out Of Scope

- Paid credentials for the default demo.
- External infrastructure that is not required by the benchmark.
- Replacing local portfolio skills with external components silently.

## Default Demo Path

- Status: implemented
- Runtime: Single non-root Python 3.12.13 container pinned by OCI digest; deterministic CPU-only benchmark with no credentials or runtime network.
- Benchmark command: `docker run --rm feature-store-lite`

## Public Proof

- Benchmark: online_read_latency_p95_ms = 45.645578341645894 ms
- Result path: `benchmarks/results/summary.json`
- Publication evidence: `benchmarks/publication/feature-store-v2.json`
