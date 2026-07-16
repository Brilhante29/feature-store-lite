from collections.abc import Mapping, Sequence
from datetime import datetime

import pytest

from feature_store_lite.application import (
    benchmark_online,
    materialize_and_prove_online,
    prove_historical,
    prove_store,
)
from feature_store_lite.domain import (
    FeatureRecord,
    FeatureVector,
    HistoricalQuery,
    historical_truth,
    latest_truth,
)
from feature_store_lite.fixture import FEATURE_TTL, build_fixture


class FakeFeatureStore:
    def __init__(self) -> None:
        self.records: tuple[FeatureRecord, ...] = ()
        self.start: datetime | None = None
        self.end: datetime | None = None
        self.sessions = 0

    def prepare(self, records: Sequence[FeatureRecord]) -> None:
        self.records = tuple(records)

    def historical(
        self,
        queries: Sequence[HistoricalQuery],
    ) -> Mapping[str, FeatureVector | None]:
        return historical_truth(self.records, queries, FEATURE_TTL)

    def materialize(self, start: datetime, end: datetime) -> float:
        self.start = start
        self.end = end
        return 0.25

    def start_online_session(self) -> None:
        self.sessions += 1

    def online(self, customer_ids: Sequence[int]) -> Mapping[int, FeatureVector]:
        assert self.start is not None and self.end is not None
        truth = latest_truth(self.records, self.start, self.end)
        return {customer_id: truth[customer_id] for customer_id in customer_ids}

    @property
    def source_sha256(self) -> str:
        return "a" * 64

    @property
    def versions(self) -> Mapping[str, str]:
        return {"fake": "1.0"}


@pytest.fixture
def prepared():
    fixture = build_fixture(entity_count=8)
    store = FakeFeatureStore()
    store.prepare(fixture.records)
    return store, fixture


def test_application_proves_historical_and_online_contracts(prepared):
    store, fixture = prepared

    historical = prove_historical(store, fixture)
    duration, online = materialize_and_prove_online(store, fixture)
    proof = prove_store(store, fixture)

    assert historical.match_rate == 1.0
    assert historical.future_leaks == 0
    assert duration == 0.25
    assert online.match_rate == 1.0
    assert proof.online.match_rate == 1.0
    assert store.sessions == 2


def test_online_benchmark_keeps_correctness_outside_timed_call(prepared):
    store, fixture = prepared
    store.materialize(fixture.materialization_start, fixture.materialization_end)

    result = benchmark_online(
        store,
        fixture,
        batch_size=4,
        iterations=3,
        warmups=1,
    )

    assert len(result.samples_ms) == 3
    assert result.p50_ms > 0
    assert result.p95_ms >= result.p50_ms
    assert result.reads_per_second > 0
    assert result.score.match_rate == 1.0


@pytest.mark.parametrize(
    ("batch_size", "iterations", "warmups", "message"),
    [
        (0, 3, 1, "batch_size"),
        (1, 2, 1, "iterations"),
        (1, 3, 0, "warmups"),
        (9, 3, 1, "exceeds"),
    ],
)
def test_online_benchmark_rejects_invalid_measurement_shapes(
    prepared,
    batch_size,
    iterations,
    warmups,
    message,
):
    store, fixture = prepared
    store.materialize(fixture.materialization_start, fixture.materialization_end)
    with pytest.raises(ValueError, match=message):
        benchmark_online(
            store,
            fixture,
            batch_size=batch_size,
            iterations=iterations,
            warmups=warmups,
        )
