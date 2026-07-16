from datetime import timedelta

import pytest

from feature_store_lite.domain import (
    FeatureVector,
    historical_truth,
    latest_truth,
    percentile,
    score_historical,
    score_online,
)
from feature_store_lite.fixture import BASE_TIMESTAMP, FEATURE_TTL, build_fixture


def test_fixture_truth_blocks_future_values_and_enforces_ttl():
    fixture = build_fixture(entity_count=8)

    assert fixture.historical_expected["eligible-1"].snapshot_sequence == 3
    assert fixture.historical_expected["ttl-null-8"] is None
    assert historical_truth(fixture.records, fixture.queries, FEATURE_TTL) == (
        fixture.historical_expected
    )


def test_historical_score_detects_a_future_leak_and_ttl_violation():
    fixture = build_fixture(entity_count=8)
    actual = dict(fixture.historical_expected)
    actual["eligible-1"] = FeatureVector(5, 15, 57.75, 0.006)
    actual["ttl-null-8"] = FeatureVector(5, 85, 59.5, 0.006)

    score = score_historical(fixture.historical_expected, actual)

    assert score.match_rate < 1.0
    assert score.future_leaks == 1
    assert score.ttl_violations == 1


def test_latest_truth_selects_newest_value_in_materialization_window():
    fixture = build_fixture(entity_count=8)

    truth = latest_truth(
        fixture.records,
        fixture.materialization_start,
        fixture.materialization_end,
    )

    assert len(truth) == 8
    assert truth[1].snapshot_sequence == 5


def test_domain_rejects_invalid_ranges_and_shapes():
    fixture = build_fixture(entity_count=8)
    with pytest.raises(ValueError, match="at least 8"):
        build_fixture(entity_count=7)
    with pytest.raises(ValueError, match="positive"):
        historical_truth(fixture.records, fixture.queries, timedelta(0))
    with pytest.raises(ValueError, match="cannot exceed"):
        latest_truth(
            fixture.records,
            BASE_TIMESTAMP + timedelta(days=1),
            BASE_TIMESTAMP,
        )
    with pytest.raises(ValueError, match="query IDs"):
        score_historical(fixture.historical_expected, {})
    with pytest.raises(ValueError, match="entity IDs"):
        score_online({1: fixture.records[0].vector()}, {})


def test_percentile_interpolates_and_validates_input():
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.5) == 2.5
    assert percentile([1.0, 2.0, 3.0, 4.0], 0.95) == pytest.approx(3.85)
    with pytest.raises(ValueError, match="empty"):
        percentile([], 0.5)
    with pytest.raises(ValueError, match="between"):
        percentile([1.0], 1.1)
