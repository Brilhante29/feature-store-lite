# Benchmark Proof: feature-store-lite

## Primary Metric

- Metric: `online_read_latency_p95_ms`
- Unit: `ms`
- Result: online_read_latency_p95_ms = 45.645578341645894 ms
- Result path: `benchmarks/results/summary.json`
- Publication path: `benchmarks/publication/feature-store-v2.json`

## Command

    ./tools/benchmark.ps1

## Evidence
- Source commit: `10641d32af027761aec62c23b0586b3c1a10992f`.
- Same immutable image across all repetitions: `sha256:cf84e303a901636d32baf1900565425f261664a2ce0575267a4daf8b334224bc`.
- p95 samples: 45.645578341645894, 53.02158489648719, and 38.05325084831566 ms.
- Median throughput: 1061.9468119765338 entity values/s.
- Correctness: 1.0 historical and online match; zero future leaks, TTL violations, and failures.

The README/post number must come from the committed benchmark JSON, not from manual text.
