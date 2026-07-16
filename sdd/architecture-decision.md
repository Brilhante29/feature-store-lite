# Architecture Decision

## Context

The repository must prove temporal consistency and online serving behavior with one local process. It does not have a user interface, remote API, distributed write path, or independently deployable services.

## Decision

Use a pipeline architecture with a hexagonal dependency boundary:

1. deterministic feature truth;
2. application port;
3. Feast adapter;
4. historical retrieval proof;
5. offline-to-online materialization;
6. online correctness proof;
7. warmup and latency measurement;
8. benchmark evidence.

Domain and application modules depend only on immutable records and the port. Feast, Pandas, PyArrow, Parquet, registry, and SQLite remain in the adapter.

## SOLID And Simplicity

- **SRP:** temporal truth, orchestration, infrastructure, and evidence have separate modules.
- **OCP/DIP:** application policy accepts any conforming feature-store port.
- **LSP:** the fake and Feast adapter must satisfy the same historical and online semantics.
- **ISP:** the port exposes only prepare, historical, materialize, online-session, online-read, and evidence metadata.
- **KISS/YAGNI:** one entity, one view, one service, and local stores; no remote server or platform.

## Rejected Styles

MVC has no view/controller problem. Microservices have no independent deployment need. Event-driven architecture has no stream or delivery guarantee. A generic layered architecture would hide the temporal stages that constitute the proof.
