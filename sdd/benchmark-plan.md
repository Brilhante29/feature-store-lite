# Benchmark Plan

## Primary Metric

`online_read_latency_p95_ms`: the 95th percentile of warmed Python SDK online-read durations.

## Fixed Signature

- FeatureService: `customer_risk_v1`.
- FeatureView: `customer_stats`.
- Features: four.
- Entities in fixture: 128.
- Entity batch size: 32.
- Warmups: 10.
- Timed iterations: 300.
- TTL: 172800 seconds.
- Offline source: Parquet.
- Online store: SQLite.
- Runtime: pinned non-root Docker image.

## Correctness Gates

Historical match 1.0, future leaks 0, TTL violations 0, online match 1.0, failures 0. The fixture truth is generated before Feast runs. Eligible historical queries have two later source snapshots; TTL queries must return null.

## Timing

Measure with `perf_counter`. Construct a fresh reader and report its first call separately. Execute warmups. For each measured iteration, start the timer immediately before `get_online_features`, stop immediately after return, then score all values.

## Evidence

Each raw JSON records all latency samples, p50/p95/p99, entity-value throughput, first read, materialization, correctness, source SHA-256, versions, environment, immutable image ID, and benchmark signature.

Run the same immutable image at least three times. Aggregate only identical project, metric, unit, image ID, and signature. Publish the median p95 with min, max, and raw results retained.

## Current Evidence

- Image: sha256:06169c2510bc9b542e33a66747f182848078e87de7e82bea5b2695366f5b78e8.
- Raw runs: benchmarks/results/raw-1.json, raw-2.json, and raw-3.json.
- Primary result: p95 median 14.985742505814416 ms, min 14.436810590268578 ms, max 16.341100465797354 ms.
- Correctness: historical match 1.0, future leaks 0, TTL violations 0, online match 1.0, failures 0 in every run.
