from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from feature_store_lite.domain import (
    HistoricalScore,
    OnlineScore,
    latest_truth,
    percentile,
    score_historical,
    score_online,
)
from feature_store_lite.fixture import FeatureFixture
from feature_store_lite.ports import FeatureStorePort


@dataclass(frozen=True, slots=True)
class OnlineBenchmark:
    first_read_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    reads_per_second: float
    samples_ms: tuple[float, ...]
    score: OnlineScore


@dataclass(frozen=True, slots=True)
class StoreProof:
    historical: HistoricalScore
    online: OnlineScore
    materialization_seconds: float


def prove_historical(
    store: FeatureStorePort,
    fixture: FeatureFixture,
) -> HistoricalScore:
    actual = store.historical(fixture.queries)
    return score_historical(fixture.historical_expected, actual)


def materialize_and_prove_online(
    store: FeatureStorePort,
    fixture: FeatureFixture,
) -> tuple[float, OnlineScore]:
    duration = store.materialize(
        fixture.materialization_start,
        fixture.materialization_end,
    )
    store.start_online_session()
    expected = latest_truth(
        fixture.records,
        fixture.materialization_start,
        fixture.materialization_end,
    )
    actual = store.online(sorted(expected))
    return duration, score_online(expected, actual)


def benchmark_online(
    store: FeatureStorePort,
    fixture: FeatureFixture,
    *,
    batch_size: int,
    iterations: int,
    warmups: int,
) -> OnlineBenchmark:
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    if iterations < 3:
        raise ValueError("iterations must be at least 3")
    if warmups < 1:
        raise ValueError("warmups must be positive")

    all_expected = latest_truth(
        fixture.records,
        fixture.materialization_start,
        fixture.materialization_end,
    )
    customer_ids = sorted(all_expected)[:batch_size]
    if len(customer_ids) != batch_size:
        raise ValueError("batch_size exceeds fixture entities")
    expected = {customer_id: all_expected[customer_id] for customer_id in customer_ids}

    store.start_online_session()
    started = perf_counter()
    first = store.online(customer_ids)
    first_read_ms = (perf_counter() - started) * 1000.0
    first_score = score_online(expected, first)
    if first_score.match_rate != 1.0:
        raise AssertionError("first online response differs from materialized truth")

    for _ in range(warmups):
        warm = store.online(customer_ids)
        if score_online(expected, warm).match_rate != 1.0:
            raise AssertionError("warmup online response differs from truth")

    samples: list[float] = []
    final_score = first_score
    for _ in range(iterations):
        started = perf_counter()
        actual = store.online(customer_ids)
        samples.append((perf_counter() - started) * 1000.0)
        final_score = score_online(expected, actual)
        if final_score.match_rate != 1.0:
            raise AssertionError("measured online response differs from truth")

    total_seconds = sum(samples) / 1000.0
    return OnlineBenchmark(
        first_read_ms=first_read_ms,
        p50_ms=percentile(samples, 0.50),
        p95_ms=percentile(samples, 0.95),
        p99_ms=percentile(samples, 0.99),
        reads_per_second=(iterations * batch_size) / total_seconds,
        samples_ms=tuple(samples),
        score=final_score,
    )


def prove_store(store: FeatureStorePort, fixture: FeatureFixture) -> StoreProof:
    historical = prove_historical(store, fixture)
    materialization_seconds, online = materialize_and_prove_online(store, fixture)
    return StoreProof(
        historical=historical,
        online=online,
        materialization_seconds=materialization_seconds,
    )
