from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from feature_store_lite.domain import FeatureRecord

CONTRACT_ID = "customer-feature-batch-v1"
FIELD_NAMES = (
    "customer_id",
    "event_timestamp",
    "created_timestamp",
    "snapshot_sequence",
    "transaction_count_7d",
    "average_order_value_30d",
    "chargeback_rate_30d",
)


@dataclass(frozen=True, slots=True)
class ValidatedFeatureBatch:
    dataset_id: str
    dataset_version: str
    contract_digest: str
    accepted_digest: str
    accepted_rows: int
    records: tuple[FeatureRecord, ...]


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_path(manifest_path: Path, uri: str) -> Path:
    if not uri or Path(uri).is_absolute():
        raise ValueError("artifact URI must be a non-empty relative path")
    base = manifest_path.parent.resolve()
    path = (base / uri).resolve()
    if base not in path.parents:
        raise ValueError("artifact URI escapes the manifest directory")
    if not path.is_file():
        raise ValueError(f"artifact does not exist: {uri}")
    return path


def _verify_artifact(manifest_path: Path, artifact: dict[str, Any]) -> Path:
    path = _artifact_path(manifest_path, str(artifact["uri"]))
    if _digest(path) != artifact["sha256"]:
        raise ValueError(f"artifact digest mismatch: {artifact['uri']}")
    with path.open(encoding="utf-8", newline="") as stream:
        rows = sum(1 for _ in csv.DictReader(stream))
    if rows != artifact["rows"]:
        raise ValueError(f"artifact row count mismatch: {artifact['uri']}")
    return path


def load_validated_feature_batch(
    manifest_path: Path,
    *,
    schema_path: Path,
    contract_path: Path,
) -> ValidatedFeatureBatch:
    manifest_path = manifest_path.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)

    if manifest["contract"]["id"] != CONTRACT_ID:
        raise ValueError("validated batch uses an incompatible data contract")
    contract_digest = _digest(contract_path)
    if manifest["contract"]["sha256"] != contract_digest:
        raise ValueError("data contract digest mismatch")

    source = _verify_artifact(manifest_path, manifest["source"])
    accepted = _verify_artifact(manifest_path, manifest["artifacts"]["accepted"])
    _verify_artifact(manifest_path, manifest["artifacts"]["quarantine"])
    quality = manifest["quality"]
    if quality["total_rows"] != quality["accepted_rows"] + quality["rejected_rows"]:
        raise ValueError("quality row counts do not reconcile")
    if sum(quality["reason_counts"].values()) < quality["rejected_rows"]:
        raise ValueError("quarantine reasons do not account for rejected rows")
    if manifest["source"]["rows"] != quality["total_rows"]:
        raise ValueError("source rows differ from quality total")
    if accepted == source and quality["rejected_rows"]:
        raise ValueError("source cannot also be accepted when rows were rejected")

    records: list[FeatureRecord] = []
    with accepted.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != FIELD_NAMES:
            raise ValueError("accepted feature columns do not match the contract")
        for row in reader:
            records.append(
                FeatureRecord(
                    customer_id=int(row["customer_id"]),
                    event_timestamp=datetime.fromisoformat(row["event_timestamp"]),
                    created_timestamp=datetime.fromisoformat(row["created_timestamp"]),
                    snapshot_sequence=int(row["snapshot_sequence"]),
                    transaction_count_7d=int(row["transaction_count_7d"]),
                    average_order_value_30d=float(row["average_order_value_30d"]),
                    chargeback_rate_30d=float(row["chargeback_rate_30d"]),
                )
            )
    return ValidatedFeatureBatch(
        dataset_id=manifest["dataset"]["id"],
        dataset_version=manifest["dataset"]["version"],
        contract_digest=contract_digest,
        accepted_digest=manifest["artifacts"]["accepted"]["sha256"],
        accepted_rows=quality["accepted_rows"],
        records=tuple(records),
    )


def write_validated_fixture(
    directory: Path,
    records: tuple[FeatureRecord, ...],
    *,
    schema_path: Path,
    contract_path: Path,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    source_path = directory / "source.csv"
    accepted_path = directory / "accepted.csv"
    quarantine_path = directory / "quarantine.csv"

    def write_rows(path: Path, values: tuple[FeatureRecord, ...]) -> None:
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELD_NAMES, lineterminator="\n")
            writer.writeheader()
            for record in values:
                writer.writerow(
                    {
                        "customer_id": record.customer_id,
                        "event_timestamp": record.event_timestamp.isoformat(),
                        "created_timestamp": record.created_timestamp.isoformat(),
                        "snapshot_sequence": record.snapshot_sequence,
                        "transaction_count_7d": record.transaction_count_7d,
                        "average_order_value_30d": record.average_order_value_30d,
                        "chargeback_rate_30d": record.chargeback_rate_30d,
                    }
                )

    write_rows(source_path, records)
    write_rows(accepted_path, records)
    write_rows(quarantine_path, ())

    def artifact(path: Path, rows: int) -> dict[str, Any]:
        return {"uri": path.name, "format": "csv", "sha256": _digest(path), "rows": rows}

    manifest = {
        "schema_version": 1,
        "dataset": {"id": "customer-features", "version": "deterministic-v1"},
        "contract": {"id": CONTRACT_ID, "sha256": _digest(contract_path)},
        "source": artifact(source_path, len(records)),
        "artifacts": {
            "accepted": artifact(accepted_path, len(records)),
            "quarantine": artifact(quarantine_path, 0),
        },
        "quality": {
            "status": "passed",
            "total_rows": len(records),
            "accepted_rows": len(records),
            "rejected_rows": 0,
            "rejected_rows_percent": 0.0,
            "reason_counts": {},
        },
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(manifest)
    manifest_path = directory / "validated-batch.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest_path
