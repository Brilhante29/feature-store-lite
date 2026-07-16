# Agent Instructions

Treat `.portfolio/` as the synchronized decision source and `project.yaml` as the public contract.

Before changing implementation, architecture, dependencies, benchmark shape, fixture timestamps, FeatureView TTL, FeatureService, provider, or store:

1. read `.codex/skills/python-feature-store/SKILL.md` or the equivalent Claude skill;
2. update the active OpenSpec change and the relevant SDD record;
3. challenge point-in-time correctness, future leakage, TTL, online-value verification, and measurement boundaries;
4. record whether the change belongs in this repository or the reuse kit;
5. invalidate benchmark evidence when the signature changes.

Keep Feast, Pandas, PyArrow, SQLite, transport, and cloud imports outside domain and application policy. Do not add Redis, an API server, a broker, orchestration, or cloud unless a measurable requirement justifies it.
