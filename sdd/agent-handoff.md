# Agent Handoff

## Current State

The repository is implementation-complete and publication evidence is current. Docker verification passes with 23 tests and 91.09% coverage. Three canonical runs from source `10641d32af027761aec62c23b0586b3c1a10992f` produced p95 median 45.645578341645894 ms, 100% historical and online correctness, zero future leaks, and zero TTL violations.

## Next Agent Procedure

1. Read `project.yaml`, `sdd/benchmark-plan.md`, and `benchmarks/publication/feature-store-v2.json`.
2. Run `./tools/validate-project.ps1` before changing the project.
3. For runtime changes, commit first and rerun `./tools/benchmark.ps1`; never edit evidence by hand.
4. Keep `validated-batch-manifest-v1` compatible with #26 and fail closed on contract, digest, reconciliation, or path violations.
5. Keep README numbers synchronized with the committed V2 evidence and verify the exact published SHA in GitHub Actions.

## Do Not

Do not replace Feast with custom joins, add Redis/API/cloud by habit, treat the first online call as warmed latency, weaken correctness gates, or publish a host-only number.
