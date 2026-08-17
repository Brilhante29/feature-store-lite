# #23 feature-store-lite: online_read_latency_p95_ms = 45.65 ms

One local-first Docker command proves point-in-time correct historical retrieval, zero future leakage, TTL behavior, deterministic Parquet-to-SQLite materialization, exact online values, and warmed Feast SDK p95 latency.

This repository belongs to the MLOps and Data Platform program. Its job is narrow: prove the measurable claim through the selected component pack before adding unrelated infrastructure or features.

The benchmark is the proof: online read p95 was 45.65 ms and median throughput was 1,061.95 entity values/s across three same-image runs. Historical and online match rates were 100%, with zero future leaks and zero TTL violations. The results are stored in `benchmarks/results/summary.json` and `benchmarks/publication/feature-store-v2.json`.

The important architecture decision is pipeline. The dominant force is an ordered evidence flow: validate the #26 batch manifest, define truth, register features, retrieve historical values, materialize, verify online values, warm up, measure, and emit immutable evidence.

The default path stays local-first. The project uses python-ml, exposes cli, uses messaging mode `none`, and stores data with `sqlite`. The dependency rule is explicit: The Feast adapter implements the application port and depends inward on immutable domain records; domain and application modules never import feature infrastructure.

The rejected work matters as much as the implemented work. Anything that does not improve the benchmark stays out of the first version.

Post angle: start with the number, show the architecture boundary, then explain which future adapter can be added without changing the core use cases.
