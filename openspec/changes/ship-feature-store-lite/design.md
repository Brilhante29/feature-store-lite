# Design

## Flow

1. Build deterministic records and historical queries.
2. Compute truth with a pure backward-time oracle and two-day TTL.
3. Write records to Parquet.
4. Apply entity, FeatureView, and `customer_risk_v1` FeatureService to Feast.
5. Retrieve historical features and score exact vectors.
6. Materialize the full source interval into SQLite.
7. Start a fresh online reader, verify first read, warm up, then measure.
8. Verify every timed response after its timer stops.
9. Emit benchmark evidence.

## Boundaries

`domain.py`, `fixture.py`, `ports.py`, and `application.py` import no feature infrastructure. `feast_adapter.py` owns every Feast/Pandas/PyArrow operation. `benchmark.py` composes the adapter and evidence.

## Failure Policy

Missing query IDs, mismatched entity IDs, null online features, any future leak, TTL violation, historical mismatch, online mismatch, invalid measurement shape, or adapter exception exits nonzero and writes failure JSON.

## Questions Revisited

- A feature server is rejected because transport is not measured.
- Airflow and MLflow remain in #21 to preserve project responsibility.
- Kumo is not invoked because no AWS behavior exists.
- The transitive FastAPI package installed by Feast is not an application boundary.
- Feature computation is excluded; the repository proves storage and retrieval semantics.
