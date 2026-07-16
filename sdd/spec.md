# Spec: feature-store-lite

## Number

#23

## Claim

One local-first Docker command proves point-in-time correct historical retrieval, zero future leakage, TTL behavior, deterministic offline-to-online materialization, exact online values, and warmed Feast SDK p95 latency.

## Problem

Training joins can silently use values created after the prediction timestamp, while serving can return features that differ from training contracts. A latency-only feature-store demo misses both failures.

## Input Contract

A deterministic Parquet dataset contains a positive `customer_id`, UTC event and creation timestamps, an increasing snapshot sequence, and three numeric model features. Six daily snapshots exist per entity.

Historical queries carry a stable query ID, entity key, and UTC event timestamp. A two-day FeatureView TTL governs eligibility.

## Outputs

- Independent historical truth keyed by query ID.
- Feast historical result and point-in-time score.
- Local registry and SQLite online materialization.
- Exact online-value score.
- Benchmark JSON with samples, p50/p95/p99, throughput, cold first read, materialization time, hashes, versions, signature, and failures.

## In Scope

- Feast local provider.
- Parquet file source.
- Local file registry.
- SQLite online store.
- Named `customer_risk_v1` FeatureService.
- Python SDK retrieval.
- Deterministic correctness and latency evidence.

## Out Of Scope

HTTP/GraphQL/gRPC serving, Redis, PostgreSQL, streaming, Airflow, MLflow, Kumo, real cloud, Kubernetes, UI, and feature computation.

## Acceptance

- Historical match rate equals 1.0.
- Future leak count equals zero.
- Expected TTL nulls are observed with zero TTL violations.
- Online value match rate equals 1.0.
- Every timed response is correctness-checked outside the timing interval.
- Default Docker path is non-root, offline, and secret-free.
- README uses only current aggregated Docker evidence.
