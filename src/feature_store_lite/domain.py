from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isclose
from typing import Mapping, Sequence

FEATURE_NAMES = (
    "snapshot_sequence",
    "transaction_count_7d",
    "average_order_value_30d",
    "chargeback_rate_30d",
)


def _require_utc(value: datetime, field: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class FeatureRecord:
    customer_id: int
    event_timestamp: datetime
    created_timestamp: datetime
    snapshot_sequence: int
    transaction_count_7d: int
    average_order_value_30d: float
    chargeback_rate_30d: float

    def __post_init__(self) -> None:
        if self.customer_id < 1:
            raise ValueError("customer_id must be positive")
        _require_utc(self.event_timestamp, "event_timestamp")
        _require_utc(self.created_timestamp, "created_timestamp")
        if self.created_timestamp < self.event_timestamp:
            raise ValueError("created_timestamp cannot precede event_timestamp")
        if self.snapshot_sequence < 0 or self.transaction_count_7d < 0:
            raise ValueError("integer features cannot be negative")
        if self.average_order_value_30d < 0:
            raise ValueError("average_order_value_30d cannot be negative")
        if not 0.0 <= self.chargeback_rate_30d <= 1.0:
            raise ValueError("chargeback_rate_30d must be between zero and one")

    def vector(self) -> FeatureVector:
        return FeatureVector(
            snapshot_sequence=self.snapshot_sequence,
            transaction_count_7d=self.transaction_count_7d,
            average_order_value_30d=self.average_order_value_30d,
            chargeback_rate_30d=self.chargeback_rate_30d,
        )


@dataclass(frozen=True, slots=True)
class HistoricalQuery:
    query_id: str
    customer_id: int
    event_timestamp: datetime

    def __post_init__(self) -> None:
        if not self.query_id:
            raise ValueError("query_id is required")
        if self.customer_id < 1:
            raise ValueError("customer_id must be positive")
        _require_utc(self.event_timestamp, "event_timestamp")


@dataclass(frozen=True, slots=True)
class FeatureVector:
    snapshot_sequence: int
    transaction_count_7d: int
    average_order_value_30d: float
    chargeback_rate_30d: float


@dataclass(frozen=True, slots=True)
class HistoricalScore:
    total: int
    matched: int
    future_leaks: int
    ttl_expected_nulls: int
    ttl_violations: int

    @property
    def match_rate(self) -> float:
        return self.matched / self.total if self.total else 0.0


@dataclass(frozen=True, slots=True)
class OnlineScore:
    total: int
    matched: int

    @property
    def match_rate(self) -> float:
        return self.matched / self.total if self.total else 0.0


def vectors_match(left: FeatureVector | None, right: FeatureVector | None) -> bool:
    if left is None or right is None:
        return left is right
    return (
        left.snapshot_sequence == right.snapshot_sequence
        and left.transaction_count_7d == right.transaction_count_7d
        and isclose(
            left.average_order_value_30d,
            right.average_order_value_30d,
            rel_tol=0.0,
            abs_tol=1e-5,
        )
        and isclose(
            left.chargeback_rate_30d,
            right.chargeback_rate_30d,
            rel_tol=0.0,
            abs_tol=1e-7,
        )
    )


def historical_truth(
    records: Sequence[FeatureRecord],
    queries: Sequence[HistoricalQuery],
    ttl: timedelta,
) -> dict[str, FeatureVector | None]:
    if ttl <= timedelta(0):
        raise ValueError("ttl must be positive")
    truth: dict[str, FeatureVector | None] = {}
    for query in queries:
        eligible = [
            record
            for record in records
            if record.customer_id == query.customer_id
            and query.event_timestamp - ttl <= record.event_timestamp <= query.event_timestamp
        ]
        chosen = max(
            eligible,
            key=lambda record: (record.event_timestamp, record.created_timestamp),
            default=None,
        )
        truth[query.query_id] = chosen.vector() if chosen else None
    return truth


def latest_truth(
    records: Sequence[FeatureRecord],
    start: datetime,
    end: datetime,
) -> dict[int, FeatureVector]:
    _require_utc(start, "start")
    _require_utc(end, "end")
    if start > end:
        raise ValueError("materialization start cannot exceed end")
    latest: dict[int, FeatureRecord] = {}
    for record in records:
        if not start <= record.event_timestamp <= end:
            continue
        current = latest.get(record.customer_id)
        if current is None or (
            record.event_timestamp,
            record.created_timestamp,
        ) > (current.event_timestamp, current.created_timestamp):
            latest[record.customer_id] = record
    return {customer_id: record.vector() for customer_id, record in latest.items()}


def score_historical(
    expected: Mapping[str, FeatureVector | None],
    actual: Mapping[str, FeatureVector | None],
) -> HistoricalScore:
    if set(expected) != set(actual):
        raise ValueError("historical result query IDs differ from truth")
    matched = 0
    future_leaks = 0
    ttl_expected_nulls = 0
    ttl_violations = 0
    for query_id, expected_vector in expected.items():
        actual_vector = actual[query_id]
        if vectors_match(expected_vector, actual_vector):
            matched += 1
        if expected_vector is None:
            ttl_expected_nulls += 1
            if actual_vector is not None:
                ttl_violations += 1
        elif (
            actual_vector is not None
            and actual_vector.snapshot_sequence > expected_vector.snapshot_sequence
        ):
            future_leaks += 1
    return HistoricalScore(
        total=len(expected),
        matched=matched,
        future_leaks=future_leaks,
        ttl_expected_nulls=ttl_expected_nulls,
        ttl_violations=ttl_violations,
    )


def score_online(
    expected: Mapping[int, FeatureVector],
    actual: Mapping[int, FeatureVector],
) -> OnlineScore:
    if set(expected) != set(actual):
        raise ValueError("online result entity IDs differ from truth")
    matched = sum(
        vectors_match(expected[customer_id], vector)
        for customer_id, vector in actual.items()
    )
    return OnlineScore(total=len(expected), matched=matched)


def percentile(samples: Sequence[float], quantile: float) -> float:
    if not samples:
        raise ValueError("samples cannot be empty")
    if not 0.0 <= quantile <= 1.0:
        raise ValueError("quantile must be between zero and one")
    ordered = sorted(samples)
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction
