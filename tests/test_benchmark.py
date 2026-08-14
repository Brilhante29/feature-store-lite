import importlib.util
import unittest
from pathlib import Path

if importlib.util.find_spec("feast") is None:
    raise unittest.SkipTest("Feast integration requires the Docker dependency set")

from feature_store_lite.benchmark import run_benchmark


def test_benchmark_writes_semantic_evidence(tmp_path: Path):
    output = tmp_path / "summary.json"

    result = run_benchmark(
        output,
        entity_count=8,
        batch_size=4,
        iterations=3,
        warmups=1,
        command="test",
    )

    assert result["metric"] == "online_read_latency_p95_ms"
    assert result["value"] > 0
    assert result["metrics"]["point_in_time_match_rate"] == 1.0
    assert result["metrics"]["future_leaks"] == 0
    assert result["metrics"]["ttl_violations"] == 0
    assert result["metrics"]["online_value_match_rate"] == 1.0
    assert result["proof"]["entity_batch_size"] == 4
    assert result["proof"]["validated_batch"]["quality_status"] == "passed"
    assert result["proof"]["validated_batch"]["accepted_rows"] == 48
    assert result["proof"]["benchmark_signature"]["validated_batch_digest"].startswith(
        "sha256:"
    )
    assert output.is_file()
