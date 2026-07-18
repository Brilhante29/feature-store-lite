from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from feature_store_lite.domain import (
    FeatureRecord,
    FeatureVector,
    HistoricalQuery,
    historical_truth,
)

BASE_TIMESTAMP = datetime(2025, 1, 1, tzinfo=UTC)
FEATURE_TTL = timedelta(days=2)


@dataclass(frozen=True, slots=True)
class FeatureFixture:
    records: tuple[FeatureRecord, ...]
    queries: tuple[HistoricalQuery, ...]
    historical_expected: dict[str, FeatureVector | None]
    materialization_start: datetime
    materialization_end: datetime


def build_fixture(entity_count: int = 128, snapshots: int = 6) -> FeatureFixture:
    if entity_count < 8:
        raise ValueError("entity_count must be at least 8")
    if snapshots < 6:
        raise ValueError("snapshots must be at least 6")

    records: list[FeatureRecord] = []
    for customer_id in range(1, entity_count + 1):
        for sequence in range(snapshots):
            event_timestamp = BASE_TIMESTAMP + timedelta(days=sequence)
            records.append(
                FeatureRecord(
                    customer_id=customer_id,
                    event_timestamp=event_timestamp,
                    created_timestamp=event_timestamp + timedelta(minutes=5),
                    snapshot_sequence=sequence,
                    transaction_count_7d=customer_id * 10 + sequence,
                    average_order_value_30d=round(
                        50.0 + customer_id * 0.25 + sequence * 1.5,
                        2,
                    ),
                    chargeback_rate_30d=round(
                        ((customer_id % 7) + sequence) / 1000.0,
                        6,
                    ),
                )
            )

    queries: list[HistoricalQuery] = []
    for customer_id in range(1, entity_count + 1):
        queries.append(
            HistoricalQuery(
                query_id=f"eligible-{customer_id}",
                customer_id=customer_id,
                event_timestamp=BASE_TIMESTAMP + timedelta(days=3, hours=12),
            )
        )
        if customer_id % 8 == 0:
            queries.append(
                HistoricalQuery(
                    query_id=f"ttl-null-{customer_id}",
                    customer_id=customer_id,
                    event_timestamp=BASE_TIMESTAMP + timedelta(days=8, hours=1),
                )
            )

    immutable_records = tuple(records)
    immutable_queries = tuple(queries)
    return FeatureFixture(
        records=immutable_records,
        queries=immutable_queries,
        historical_expected=historical_truth(
            immutable_records,
            immutable_queries,
            FEATURE_TTL,
        ),
        materialization_start=BASE_TIMESTAMP,
        materialization_end=BASE_TIMESTAMP + timedelta(days=snapshots - 1, hours=1),
    )
