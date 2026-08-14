from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from statistics import median
from typing import Any


def nested(value: dict[str, Any], dotted_path: str) -> Any:
    current: Any = value
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise ValueError(f"missing required result path: {dotted_path}")
        current = current[part]
    return current


def load_result(
    path: Path,
    project: str,
    metric: str,
    unit: str,
) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if result.get("project") != project:
        raise ValueError(f"{path} belongs to another project")
    if result.get("metric") != metric or result.get("unit") != unit:
        raise ValueError(f"{path} has an incompatible benchmark contract")
    if result.get("failures") != 0:
        raise ValueError(f"{path} contains benchmark failures")
    return result


def aggregate_results(
    paths: list[Path],
    output: Path,
    project: str,
    metric: str,
    unit: str,
    summary_metrics: tuple[str, ...],
    signature_path: str,
    image_path: str = "environment.image_id",
) -> dict[str, Any]:
    if len(paths) < 3:
        raise ValueError("at least three raw benchmark results are required")
    loaded = [load_result(path, project, metric, unit) for path in paths]

    image_ids = {nested(result, image_path) for result in loaded}
    if len(image_ids) != 1 or image_ids == {"not-recorded"} or None in image_ids:
        raise ValueError("all runs must record the same immutable image ID")

    signatures = {
        json.dumps(nested(result, signature_path), sort_keys=True)
        for result in loaded
    }
    if len(signatures) != 1:
        raise ValueError("all runs must contain the same benchmark signature")

    result = deepcopy(loaded[0])
    result["timestamp"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    result["value"] = median(float(item["value"]) for item in loaded)
    result["repeat"] = len(loaded)
    result["results"] = [path.name for path in paths]
    result["environment"]["aggregated_runs"] = len(loaded)
    result["summary"] = {}
    result["metrics"] = {}
    for name in summary_metrics:
        samples = [float(nested(item, f"metrics.{name}")) for item in loaded]
        result["summary"][name] = median(samples)
        result["metrics"][name] = {
            "median": median(samples),
            "min": min(samples),
            "max": max(samples),
            "samples": samples,
        }

    result["proof"] = {
        "aggregate": "median with min, max, and all samples",
        "raw_results": [path.name for path in paths],
        "image_id": next(iter(image_ids)),
        "signature_path": signature_path,
        "signature": json.loads(next(iter(signatures))),
        "all_failures_preserved": True,
        "source_proof": loaded[0].get("proof", {}),
    }
    result["failures"] = sum(int(item["failures"]) for item in loaded)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--metric", required=True)
    parser.add_argument("--unit", required=True)
    parser.add_argument("--summary-metric", action="append", required=True)
    parser.add_argument("--signature-path", required=True)
    parser.add_argument("--image-path", default="environment.image_id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("inputs", nargs="+", type=Path)
    args = parser.parse_args()
    result = aggregate_results(
        paths=sorted(args.inputs),
        output=args.output,
        project=args.project,
        metric=args.metric,
        unit=args.unit,
        summary_metrics=tuple(args.summary_metric),
        signature_path=args.signature_path,
        image_path=args.image_path,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
