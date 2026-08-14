from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import uuid
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


def git_blob(root: Path, commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), "show", f"{commit}:{path}"],
        check=True,
        capture_output=True,
    ).stdout


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def metric(
    name: str,
    values: list[float],
    unit: str,
    direction: str,
    failures: int,
) -> dict[str, Any]:
    return {
        "name": name,
        "value": statistics.median(values),
        "unit": unit,
        "direction": direction,
        "samples": values,
        "failures": failures,
        "summary": {
            "min": min(values),
            "max": max(values),
            "mean": statistics.fmean(values),
            "median": statistics.median(values),
        },
    }


def effective_workload(
    template: dict[str, Any],
    *,
    entities: int,
    batch_size: int,
    iterations: int,
    warmups: int,
    repetitions: int,
) -> dict[str, Any]:
    effective = dict(template)
    effective.update(
        {
            "entity_count": entities,
            "entity_batch_size": batch_size,
            "measured_requests_per_repetition": iterations,
            "warmup_requests": warmups,
            "repetitions": repetitions,
        }
    )
    return effective


def build(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    workload_template = json.loads(git_blob(root, args.source_commit, args.workload_ref))
    workload = effective_workload(
        workload_template,
        entities=args.entities,
        batch_size=args.batch_size,
        iterations=args.iterations,
        warmups=args.warmups,
        repetitions=args.repetitions,
    )
    runs = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(Path(args.results_directory).glob("run-*.json"))
    ]
    if len(runs) != args.repetitions:
        raise ValueError("raw run count differs from workload repetitions")

    expected_shape = (args.entities, args.batch_size, args.iterations, args.warmups)
    for run in runs:
        proof = run["proof"]
        actual_shape = (
            int(proof["entity_count"]),
            int(proof["entity_batch_size"]),
            int(proof["iterations"]),
            int(proof["warmups"]),
        )
        if actual_shape != expected_shape:
            raise ValueError("raw run shape differs from executed workload")
    failures = sum(int(run["failures"]) for run in runs)
    if failures:
        raise ValueError(f"benchmark runs contain {failures} failure(s)")

    def samples(field: str) -> list[float]:
        return [float(run["metrics"][field]) for run in runs]

    metrics = [
        metric(
            "online_read_latency_p95_ms",
            samples("online_read_p95_ms"),
            "milliseconds",
            "lower_is_better",
            failures,
        ),
        metric(
            "online_read_latency_p50_ms",
            samples("online_read_p50_ms"),
            "milliseconds",
            "lower_is_better",
            failures,
        ),
        metric(
            "online_read_latency_p99_ms",
            samples("online_read_p99_ms"),
            "milliseconds",
            "lower_is_better",
            failures,
        ),
        metric(
            "online_entity_values_per_second",
            samples("online_entity_values_per_second"),
            "entity_values_per_second",
            "higher_is_better",
            failures,
        ),
        metric(
            "point_in_time_match_rate",
            samples("point_in_time_match_rate"),
            "ratio",
            "higher_is_better",
            failures,
        ),
        metric(
            "online_value_match_rate",
            samples("online_value_match_rate"),
            "ratio",
            "higher_is_better",
            failures,
        ),
        metric("future_leak_count", samples("future_leaks"), "count", "target", failures),
        metric("ttl_violation_count", samples("ttl_violations"), "count", "target", failures),
    ]
    first = runs[0]
    fixture_digest = first["proof"]["validated_batch"]["accepted_digest"]
    if any(
        run["proof"]["validated_batch"]["accepted_digest"] != fixture_digest
        for run in runs
    ):
        raise ValueError("validated batch digest differs between repetitions")

    result = {
        "schema_version": 2,
        "run_id": str(uuid.uuid4()),
        "project": "feature-store-lite",
        "benchmark_id": workload["benchmark_id"],
        "workload": {
            "version": "customer-risk-features-v1",
            "fixture_digest": fixture_digest,
            "config_digest": digest(
                json.dumps(workload, sort_keys=True, separators=(",", ":")).encode()
            ),
            "warmup_iterations": args.warmups,
            "measured_iterations": args.iterations,
            "concurrency": workload["concurrency"],
        },
        "metrics": metrics,
        "execution": {
            "command": args.command,
            "started_at": min(run["started_at"] for run in runs),
            "duration_seconds": sum(float(run["duration_seconds"]) for run in runs),
            "exit_code": 0,
            "repeat": len(runs),
        },
        "environment": {
            "runtime": f"python-{first['environment']['python']}",
            "architecture": first["environment"]["machine"],
            "hardware_class": args.hardware_class,
            "container_platform": first["environment"]["platform"],
            "feast": first["environment"]["feast"],
            "pandas": first["environment"]["pandas"],
            "pyarrow": first["environment"]["pyarrow"],
            "online_store": "sqlite",
        },
        "provenance": {
            "source_commit": args.source_commit,
            "clean_tree": True,
            "image_ref": args.image_ref,
            "image_digest": args.image_digest,
            "dependency_lock_digest": digest(
                git_blob(root, args.source_commit, args.lock_ref)
            ),
            "producer": args.producer,
            "artifact_digest": args.artifact_digest,
        },
        "comparability_key": (
            "feature-store-lite:customer-risk-v1:"
            f"entities-{args.entities}:batch-{args.batch_size}:"
            f"requests-{args.iterations}:warmups-{args.warmups}:"
            "feast-0_64_0:sqlite"
        ),
    }
    schema = json.loads(
        (root / ".portfolio/contracts/benchmark-result-v2.schema.json").read_text(
            encoding="utf-8"
        )
    )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(result)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--results-directory", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--image-ref", required=True)
    parser.add_argument("--image-digest", required=True)
    parser.add_argument("--artifact-digest", required=True)
    parser.add_argument("--hardware-class", required=True)
    parser.add_argument("--entities", type=int, required=True)
    parser.add_argument("--batch-size", type=int, required=True)
    parser.add_argument("--iterations", type=int, required=True)
    parser.add_argument("--warmups", type=int, required=True)
    parser.add_argument("--repetitions", type=int, required=True)
    parser.add_argument(
        "--producer", choices=("local", "github-actions", "other-ci"), required=True
    )
    parser.add_argument("--workload-ref", default="benchmarks/workload.json")
    parser.add_argument("--lock-ref", default="constraints.lock")
    parser.add_argument("--command", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build(args), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
