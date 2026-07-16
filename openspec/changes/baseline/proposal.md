# Change Proposal: baseline

Project: `feature-store-lite` (#23)

## Intent

One local-first Docker command proves point-in-time correct historical retrieval, zero future leakage, TTL behavior, deterministic Parquet-to-SQLite materialization, exact online values, and warmed Feast SDK p95 latency.

## Why This Change Exists

Describe the smallest change that improves the measurable claim or removes a
known portfolio risk.

## Scope

- In scope: <scope>
- Out of scope: paid credentials, unrelated infrastructure, and unmeasured features.

## Portfolio Impact

Program: `mlops-data-platform`

This change should produce evidence, fixtures, decisions, or components that
can be reused by sibling repositories without moving project-specific behavior
into the kit.

## Acceptance Signal

The benchmark in `project.yaml` remains reproducible and its result is recorded
in `benchmarks/results/`.
