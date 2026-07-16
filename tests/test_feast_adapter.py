from pathlib import Path

import importlib.util
import unittest

import pytest

if importlib.util.find_spec("feast") is None:
    raise unittest.SkipTest("Feast integration requires the Docker dependency set")

from feature_store_lite.application import materialize_and_prove_online, prove_historical
from feature_store_lite.feast_adapter import FeastFeatureStore
from feature_store_lite.fixture import build_fixture


def test_feast_adapter_matches_independent_historical_and_online_truth(tmp_path: Path):
    fixture = build_fixture(entity_count=8)
    store = FeastFeatureStore(tmp_path)
    store.prepare(fixture.records)

    historical = prove_historical(store, fixture)
    duration, online = materialize_and_prove_online(store, fixture)

    assert historical.match_rate == 1.0
    assert historical.future_leaks == 0
    assert historical.ttl_violations == 0
    assert online.match_rate == 1.0
    assert duration > 0
    assert len(store.source_sha256) == 64
    assert store.versions["feast"] == "0.64.0"


def test_adapter_rejects_unprepared_and_empty_operations(tmp_path: Path):
    store = FeastFeatureStore(tmp_path)
    with pytest.raises(RuntimeError, match="not been prepared"):
        _ = store.store
    with pytest.raises(RuntimeError, match="before prepare"):
        _ = store.source_sha256
    with pytest.raises(ValueError, match="empty"):
        store.prepare([])
