# Architecture Record: feature-store-lite

## Decision

- Architecture: `pipeline`
- Stack profile: `python-ml`
- API style: `cli`
- Messaging: `none`
- Database/runtime: `sqlite` / `Single non-root Python 3.12.13 container pinned by OCI digest; deterministic CPU-only benchmark with no credentials or runtime network.`

## Reason

The dominant force is an ordered evidence flow: define truth, register features, retrieve historical values, materialize, verify online values, warm up, measure, and emit immutable evidence.

## Dependency Direction

The Feast adapter implements the application port and depends inward on immutable domain records; domain and application modules never import feature infrastructure.

## Boundaries

- deterministic temporal fixture and independent oracle
- feature-store application port
- Feast local-provider adapter
- Parquet offline source
- local file registry
- SQLite online store
- correctness and benchmark evidence

## Library Policy

Feast owns feature-store semantics; Pandas and PyArrow only serialize deterministic Parquet fixtures and bridge Feast results. SQLite is sufficient for the single-process local latency claim. Redis requires a separate concurrency hypothesis.

## Principle Check

- SRP: keep benchmark, API, use cases, and adapters separate.
- OCP: new providers must be adapters, not domain rewrites.
- LSP: replacement providers must preserve observable behavior.
- ISP: ports stay narrow.
- DIP: application depends on behavior, not infrastructure.
- KISS/YAGNI: leave out anything that does not improve the benchmark.
