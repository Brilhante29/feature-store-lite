# Proposal: ship feature-store-lite

## Why

A portfolio feature store must prove more than low latency. It must demonstrate that training retrieval never sees the future, TTL is enforced, serving returns the materialized values expected by the model contract, and the latency number has a stable measurement shape.

## What Changes

Build a deterministic Feast local-provider repository with Parquet offline data, a local registry, SQLite online storage, one named FeatureService, an independent temporal oracle, semantic benchmark JSON, Docker, tests, and CI.

## OpenSpec Self-Challenge

### Could a custom Python join be simpler?

It would be shorter, but it would prove only our join code. Use the custom logic solely as an independent oracle and exercise Feast as the production engine.

### Should Redis represent production?

Not in this claim. Redis is justified only by concurrent processes or a network-serving hypothesis. SQLite is the smallest real Feast online store for a local SDK benchmark.

### Is latency enough?

No. Historical match, future leaks, TTL violations, online value match, and failures are hard gates.

### Does a port over-abstract Feast?

The port isolates temporal application policy and enables a substitutability test. It has one real adapter and one test fake, so it removes framework coupling without speculative plugin machinery.

## Success

One Docker command emits valid semantic evidence; three same-image runs aggregate into a current README result; strict validation and CI pass.
