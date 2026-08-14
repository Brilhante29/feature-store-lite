import importlib.util
from pathlib import Path


def load_producer():
    path = Path("tools/build_v2_evidence.py")
    spec = importlib.util.spec_from_file_location("build_v2_evidence", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_effective_workload_uses_executed_smoke_shape():
    producer = load_producer()
    template = {
        "entity_count": 128,
        "entity_batch_size": 32,
        "measured_requests_per_repetition": 300,
        "warmup_requests": 10,
        "repetitions": 3,
    }

    smoke = producer.effective_workload(
        template,
        entities=8,
        batch_size=4,
        iterations=3,
        warmups=1,
        repetitions=3,
    )

    assert smoke["entity_count"] == 8
    assert smoke["entity_batch_size"] == 4
    assert smoke["measured_requests_per_repetition"] == 3
    assert smoke["warmup_requests"] == 1
    assert smoke["repetitions"] == 3
    assert template["entity_count"] == 128
