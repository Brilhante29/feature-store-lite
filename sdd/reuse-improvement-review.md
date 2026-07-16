# Reuse Improvement Review

## Question

What did #23 need that the reuse kit could not previously decide or enforce?

## Finding

The kit named Feast patterns but still cataloged FastAPI, PostgreSQL, and Redis by default. It lacked guidance for point-in-time truth, future leakage, TTL cases, FeatureService stability, materialization proof, cold-versus-warm timing, and the threshold for introducing Redis or cloud.

## Decision

Patch the kit before completing the project:

- add `python-feature-store` skills for Codex and Claude;
- add the feature-store standard;
- update the Python profile and MLOps component pack;
- replace the catalog stack with Feast, Parquet, and SQLite;
- add validation gates for both agent skills and the new benchmark metric.

## Local-Only Knowledge

Customer feature formulas, entity count, timestamps, FeatureService name, and benchmark signature remain project-specific.

## Status

Patched in staging and validated. Runtime behavior must still be verified in Docker before the kit change and project are published.

## Final Gate

- [x] Reusable improvements were patched or recorded.
- [x] Project-specific implementation was not moved into the kit.
- [x] Validation reflects feature-store skills, catalog, profile, component pack, and documentation.
