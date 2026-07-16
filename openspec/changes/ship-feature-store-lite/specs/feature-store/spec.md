# Feature Store Requirements

## Historical Retrieval

The system SHALL retrieve the latest feature row whose event timestamp is not later than each query and is within the FeatureView TTL.

The system SHALL define expected vectors before Feast retrieval. The fixture SHALL contain later source rows for every eligible query and at least one expected TTL null.

## Model Contract

The system SHALL expose features through the named `customer_risk_v1` FeatureService.

## Materialization

The system SHALL record the materialization interval and duration. Online retrieval SHALL match the newest source vector inside that interval for every checked entity.

## Benchmark

The system SHALL time warmed SDK calls with fixed feature count, entity batch, warmups, and iterations. It SHALL report all samples, p50, p95, p99, throughput, first read, correctness, versions, source hash, signature, image ID, and failures.

## Local First

The default Docker path SHALL use Parquet, local registry, and SQLite without credentials or runtime network access. Cloud and Redis SHALL remain optional future adapters justified by separate acceptance criteria.
