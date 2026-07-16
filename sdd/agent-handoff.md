# Agent Handoff

## Current State

Implementation, pure tests, Feast integration tests, Dockerfile, CI, SDD, and OpenSpec are complete in staging. Docker execution, immutable image evidence, aggregation, strict validation, Desktop synchronization, commit, push, and GitHub Actions remain blocked by the current environment limit.

## Next Agent Procedure

1. Read `project.yaml`, `sdd/benchmark-plan.md`, and the feature-store skill.
2. Build `feature-store-lite`.
3. Run Ruff and all tests in the image; no Feast adapter test may skip.
4. Inspect dependency freeze and image ID.
5. Run one short semantic benchmark and validate JSON.
6. Run three full benchmarks from the same image with unique output names and `IMAGE_ID` set.
7. Aggregate through `.portfolio/harness/aggregate_results.py` using `proof.benchmark_signature`.
8. Run strict `tools/validate-project.ps1`.
9. Update README only from `summary.json`.
10. Re-run validation, publish, and inspect Actions.

## Do Not

Do not replace Feast with custom joins, add Redis/API/cloud by habit, treat the first online call as warmed latency, weaken correctness gates, or publish a host-only number.
