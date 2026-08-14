from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from feature_store_lite.benchmark import run_benchmark


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="feature-store-lite")
    subparsers = parser.add_subparsers(dest="command", required=True)
    benchmark = subparsers.add_parser("benchmark")
    benchmark.add_argument("--entities", type=int, default=128)
    benchmark.add_argument("--batch-size", type=int, default=32)
    benchmark.add_argument("--iterations", type=int, default=300)
    benchmark.add_argument("--warmups", type=int, default=10)
    benchmark.add_argument("--validated-batch-manifest", type=Path)
    benchmark.add_argument(
        "--output",
        type=Path,
        default=Path(
            os.getenv(
                "BENCHMARK_OUTPUT",
                "benchmarks/results/summary.json",
            )
        ),
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    arguments = list(argv if argv is not None else sys.argv[1:])
    if not arguments:
        arguments = ["benchmark"]
    args = build_parser().parse_args(arguments)
    result = run_benchmark(
        args.output,
        entity_count=args.entities,
        batch_size=args.batch_size,
        iterations=args.iterations,
        warmups=args.warmups,
        validated_batch_manifest=args.validated_batch_manifest,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def main() -> int:
    try:
        return run()
    except Exception as error:
        failure = {
            "project": "feature-store-lite",
            "timestamp": datetime.now(UTC)
            .isoformat()
            .replace("+00:00", "Z"),
            "error_type": type(error).__name__,
            "error": str(error),
        }
        path = Path("benchmarks/results/failure.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(failure, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(json.dumps(failure, sort_keys=True), file=sys.stderr)
        return 1
