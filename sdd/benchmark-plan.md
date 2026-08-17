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

- Source commit: `10641d32af027761aec62c23b0586b3c1a10992f`.
- Image: `sha256:cf84e303a901636d32baf1900565425f261664a2ce0575267a4daf8b334224bc`.
- Wheel: `sha256:eae158ceb9e9b1edbb02713025a4ca255ff776f7179b3ad5ac0be35d5efba5a9`.
- Raw runs: `benchmarks/results/run-1.json`, `run-2.json`, and `run-3.json`; V1 aggregate and V2 publication evidence are committed.
- Primary result: p95 median 45.645578341645894 ms, min 38.05325084831566 ms, max 53.02158489648719 ms.
- Throughput: median 1061.9468119765338 entity values/s.
- Correctness: historical match 1.0, future leaks 0, TTL violations 0, online match 1.0, failures 0 in every run.
