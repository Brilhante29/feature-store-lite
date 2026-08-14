import json
from pathlib import Path

import pytest

from feature_store_lite.fixture import build_fixture
from feature_store_lite.validated_batch import (
    load_validated_feature_batch,
    write_validated_fixture,
)

SCHEMA = Path("contracts/validated-batch-manifest-v1.schema.json")
CONTRACT = Path("contracts/customer-feature-batch-v1.contract.json")


def make_batch(tmp_path: Path):
    fixture = build_fixture(entity_count=8)
    manifest = write_validated_fixture(
        tmp_path,
        fixture.records,
        schema_path=SCHEMA,
        contract_path=CONTRACT,
    )
    return fixture, manifest


def test_validated_batch_round_trip_preserves_domain_records(tmp_path: Path):
    fixture, manifest = make_batch(tmp_path)

    batch = load_validated_feature_batch(
        manifest,
        schema_path=SCHEMA,
        contract_path=CONTRACT,
    )

    assert batch.records == fixture.records
    assert batch.accepted_rows == 48
    assert batch.dataset_id == "customer-features"
    assert batch.accepted_digest.startswith("sha256:")


def test_validated_batch_fails_closed_on_artifact_tampering(tmp_path: Path):
    _, manifest = make_batch(tmp_path)
    accepted = tmp_path / "accepted.csv"
    accepted.write_text(accepted.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="digest mismatch"):
        load_validated_feature_batch(
            manifest,
            schema_path=SCHEMA,
            contract_path=CONTRACT,
        )


def test_validated_batch_rejects_unknown_contract(tmp_path: Path):
    _, manifest = make_batch(tmp_path)
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["contract"]["id"] = "unknown-v1"
    manifest.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="incompatible data contract"):
        load_validated_feature_batch(
            manifest,
            schema_path=SCHEMA,
            contract_path=CONTRACT,
        )


def test_validated_batch_rejects_path_escape(tmp_path: Path):
    _, manifest = make_batch(tmp_path / "batch")
    outside = tmp_path / "outside.csv"
    outside.write_text("customer_id\n", encoding="utf-8")
    value = json.loads(manifest.read_text(encoding="utf-8"))
    value["artifacts"]["accepted"]["uri"] = "../outside.csv"
    manifest.write_text(json.dumps(value), encoding="utf-8")

    with pytest.raises(ValueError, match="escapes"):
        load_validated_feature_batch(
            manifest,
            schema_path=SCHEMA,
            contract_path=CONTRACT,
        )
