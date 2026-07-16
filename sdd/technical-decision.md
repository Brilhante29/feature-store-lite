# Technical Decision: feature-store-lite

## Stack

- Python 3.12.13 slim image pinned by OCI digest.
- Feast 0.64.0.
- Pandas 2.3.3.
- PyArrow 25.0.0.
- Parquet offline source.
- Feast local file registry.
- SQLite online store.
- Docker non-root UID 10001.

## Why Feast

The claim requires registry semantics, point-in-time joins, FeatureService contracts, materialization, and online retrieval. Feast supplies those behaviors as a proven Apache-2.0 project. The repository owns independent truth and evidence instead of reimplementing the engine.

## Why Local Files And SQLite

The measured claim is single-process local SDK retrieval. Parquet and SQLite exercise the real offline/online separation while keeping one-container execution deterministic. Redis would add a networked process but prove nothing about concurrency because no concurrent workload exists.

## Feature Contract

`customer_risk_v1` is the named model-facing FeatureService. It includes one FeatureView with four fields and a two-day TTL. Application code retrieves the service from the registry instead of assembling ad hoc feature references.

## Rejections

- **FastAPI/custom CRUD:** proves transport, not feature-store semantics.
- **Redis/PostgreSQL:** no multi-process concurrency or SQL workload.
- **Airflow:** no schedule, retry, backfill, or DAG claim.
- **MLflow:** model lifecycle belongs to #21.
- **Kafka/RabbitMQ:** no stream or delivery guarantee.
- **Kumo/AWS:** no cloud behavior.
- **Custom point-in-time join:** weaker and riskier than a proven engine.

## Measurement Boundary

Fixture creation, Parquet write, apply, historical retrieval, materialization, first online reader construction, first read, correctness scoring, and JSON output are outside warmed latency samples. Each sample times one SDK online call for a fixed entity batch and feature count. Correctness is checked immediately after the timer stops.

## Dependency Note

Feast may install web-framework packages transitively. They are not imported by project code and do not make HTTP part of the architecture.

## Docker Verification Pending

The exact Feast/Pandas/PyArrow API, all adapter tests, lint, coverage, transitive freeze, immutable image ID, and three full benchmark runs must execute in Docker before publication.
