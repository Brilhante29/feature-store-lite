from __future__ import annotations

import json
import os
import platform
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from feature_store_lite.application import (
    benchmark_online,
    materialize_and_prove_online,
    prove_historical,
)
from feature_store_lite.fixture import FEATURE_TTL, build_fixture


def run_benchmark(
    output_path: Path | None,
    *,
    entity_count: int = 128,
    batch_size: int = 32,
    iterations: int = 300,
    warmups: int = 10,
    command: str = "docker run --rm feature-store-lite",
) -> dict[str, Any]:
    from feature_store_lite.feast_adapter import FeastFeatureStore

    fixture = build_fixture(entity_count=entity_count)
    with tempfile.TemporaryDirectory(prefix="feature-store-lite-") as temporary:
        store = FeastFeatureStore(Path(temporary))
        store.prepare(fixture.records)

        historical = prove_historical(store, fixture)
        materialization_seconds, online_score = materialize_and_prove_online(
            store,
            fixture,
        )
        online = benchmark_online(
            store,
            fixture,
            batch_size=batch_size,
            iterations=iterations,
            warmups=warmups,
        )
        if historical.match_rate != 1.0:
            raise AssertionError("historical retrieval differs from independent truth")
        if historical.future_leaks or historical.ttl_violations:
            raise AssertionError("point-in-time or TTL proof failed")
        if online_score.match_rate != 1.0 or online.score.match_rate != 1.0:
            raise AssertionError("online retrieval differs from materialized truth")

        versions = store.versions
        result = {
            "project": "feature-store-lite",
            "metric": "online_read_latency_p95_ms",
            "value": online.p95_ms,
            "unit": "ms",
            "timestamp": datetime.now(UTC)
            .isoformat()
            .replace("+00:00", "Z"),
            "command": command,
            "repeat": 1,
            "samples": list(online.samples_ms),
            "environment": {
                "python": platform.python_version(),
                "implementation": platform.python_implementation(),
                "platform": platform.platform(),
                "machine": platform.machine(),
                "feast": versions["feast"],
                "pandas": versions["pandas"],
                "pyarrow": versions["pyarrow"],
                "container": Path("/.dockerenv").exists(),
                "image_id": os.getenv("IMAGE_ID", "not-recorded"),
            },
            "summary": {
                "online_read_p50_ms": online.p50_ms,
                "online_read_p95_ms": online.p95_ms,
                "online_read_p99_ms": online.p99_ms,
                "online_entity_values_per_second": online.reads_per_second,
                "first_online_read_ms": online.first_read_ms,
                "materialization_seconds": materialization_seconds,
                "point_in_time_match_rate": historical.match_rate,
                "online_value_match_rate": online.score.match_rate,
            },
            "metrics": {
                "historical_queries": historical.total,
                "historical_matches": historical.matched,
                "point_in_time_match_rate": historical.match_rate,
                "future_leaks": historical.future_leaks,
                "ttl_expected_nulls": historical.ttl_expected_nulls,
                "ttl_violations": historical.ttl_violations,
                "online_entities_checked": online.score.total,
                "online_value_match_rate": online.score.match_rate,
                "first_online_read_ms": online.first_read_ms,
                "online_read_p50_ms": online.p50_ms,
                "online_read_p95_ms": online.p95_ms,
                "online_read_p99_ms": online.p99_ms,
                "online_entity_values_per_second": online.reads_per_second,
                "materialization_seconds": materialization_seconds,
            },
            "proof": {
                "feature_service": "customer_risk_v1",
                "feature_view": "customer_stats",
                "feature_count": 4,
                "entity_count": entity_count,
                "entity_batch_size": batch_size,
                "iterations": iterations,
                "warmups": warmups,
                "fixture_rows": len(fixture.records),
                "source_sha256": store.source_sha256,
                "ttl_seconds": int(FEATURE_TTL.total_seconds()),
                "future_rows_exist_for_eligible_queries": True,
                "truth_defined_before_retrieval": True,
                "offline_store": "Parquet file source",
                "online_store": "SQLite",
                "registry": "local file registry",
                "measurement_boundary": "warmed Python SDK get_online_features call",
                "benchmark_signature": {
                    "feature_service": "customer_risk_v1",
                    "feature_count": 4,
                    "entity_count": entity_count,
                    "entity_batch_size": batch_size,
                    "iterations": iterations,
                    "warmups": warmups,
                    "ttl_seconds": int(FEATURE_TTL.total_seconds()),
                    "source_sha256": store.source_sha256,
                    "offline_store": "parquet",
                    "online_store": "sqlite",
                },
            },
            "failures": 0,
        }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    return result
