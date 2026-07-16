from __future__ import annotations

import hashlib
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from time import perf_counter
from typing import Any, Sequence

import pandas as pd
import pyarrow
from feast import Entity, FeatureService, FeatureStore, FeatureView, Field, FileSource
from feast.types import Float64, Int64

from feature_store_lite.domain import (
    FEATURE_NAMES,
    FeatureRecord,
    FeatureVector,
    HistoricalQuery,
)
from feature_store_lite.fixture import FEATURE_TTL

VIEW_NAME = "customer_stats"
SERVICE_NAME = "customer_risk_v1"


def _response_column(data: dict[str, list[Any]], name: str) -> list[Any]:
    if name in data:
        return data[name]
    suffix = f"__{name}"
    candidates = [values for key, values in data.items() if key.endswith(suffix)]
    if len(candidates) != 1:
        raise ValueError(f"response does not contain one column for {name}")
    return candidates[0]


def _vector_from_columns(
    columns: dict[str, list[Any]],
    index: int,
) -> FeatureVector | None:
    sequence = _response_column(columns, "snapshot_sequence")[index]
    if pd.isna(sequence):
        return None
    return FeatureVector(
        snapshot_sequence=int(sequence),
        transaction_count_7d=int(
            _response_column(columns, "transaction_count_7d")[index]
        ),
        average_order_value_30d=float(
            _response_column(columns, "average_order_value_30d")[index]
        ),
        chargeback_rate_30d=float(
            _response_column(columns, "chargeback_rate_30d")[index]
        ),
    )


class FeastFeatureStore:
    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path.resolve()
        self.data_path = self.repo_path / "data"
        self.parquet_path = self.data_path / "customer_features.parquet"
        self._store: FeatureStore | None = None
        self._online_reader: FeatureStore | None = None
        self._source_sha256 = ""

    @property
    def store(self) -> FeatureStore:
        if self._store is None:
            raise RuntimeError("feature store has not been prepared")
        return self._store

    def prepare(self, records: Sequence[FeatureRecord]) -> None:
        if not records:
            raise ValueError("records cannot be empty")
        self.data_path.mkdir(parents=True, exist_ok=True)
        self._write_config()
        frame = pd.DataFrame(
            [
                {
                    "customer_id": record.customer_id,
                    "event_timestamp": record.event_timestamp,
                    "created_timestamp": record.created_timestamp,
                    "snapshot_sequence": record.snapshot_sequence,
                    "transaction_count_7d": record.transaction_count_7d,
                    "average_order_value_30d": record.average_order_value_30d,
                    "chargeback_rate_30d": record.chargeback_rate_30d,
                }
                for record in records
            ]
        )
        frame.to_parquet(self.parquet_path, index=False)
        self._source_sha256 = hashlib.sha256(self.parquet_path.read_bytes()).hexdigest()

        source = FileSource(
            name="customer_features_source",
            path=str(self.parquet_path),
            timestamp_field="event_timestamp",
            created_timestamp_column="created_timestamp",
        )
        customer = Entity(
            name="customer",
            join_keys=["customer_id"],
            description="Stable customer entity used by the risk model.",
        )
        customer_stats = FeatureView(
            name=VIEW_NAME,
            entities=[customer],
            ttl=FEATURE_TTL,
            schema=[
                Field(name="snapshot_sequence", dtype=Int64),
                Field(name="transaction_count_7d", dtype=Int64),
                Field(name="average_order_value_30d", dtype=Float64),
                Field(name="chargeback_rate_30d", dtype=Float64),
            ],
            source=source,
            online=True,
        )
        service = FeatureService(
            name=SERVICE_NAME,
            features=[customer_stats],
            description="Immutable v1 input contract for the customer risk model.",
        )
        self._store = FeatureStore(repo_path=str(self.repo_path))
        self._store.apply([customer, customer_stats, service])
        self._online_reader = None

    def historical(
        self,
        queries: Sequence[HistoricalQuery],
    ) -> dict[str, FeatureVector | None]:
        entity_frame = pd.DataFrame(
            [
                {
                    "query_id": query.query_id,
                    "customer_id": query.customer_id,
                    "event_timestamp": query.event_timestamp,
                }
                for query in queries
            ]
        )
        service = self.store.get_feature_service(SERVICE_NAME)
        result = self.store.get_historical_features(
            entity_df=entity_frame,
            features=service,
        ).to_df()
        columns = result.to_dict(orient="list")
        query_ids = columns["query_id"]
        return {
            str(query_id): _vector_from_columns(columns, index)
            for index, query_id in enumerate(query_ids)
        }

    def materialize(self, start: datetime, end: datetime) -> float:
        started = perf_counter()
        self.store.materialize(
            start_date=start,
            end_date=end,
            feature_views=[VIEW_NAME],
        )
        return perf_counter() - started

    def start_online_session(self) -> None:
        self._online_reader = FeatureStore(repo_path=str(self.repo_path))

    def online(self, customer_ids: Sequence[int]) -> dict[int, FeatureVector]:
        if not customer_ids:
            raise ValueError("customer_ids cannot be empty")
        reader = self._online_reader or self.store
        service = reader.get_feature_service(SERVICE_NAME)
        response = reader.get_online_features(
            features=service,
            entity_rows=[{"customer_id": customer_id} for customer_id in customer_ids],
            full_feature_names=False,
        ).to_dict()
        entity_values = _response_column(response, "customer_id")
        output: dict[int, FeatureVector] = {}
        for index, customer_id in enumerate(entity_values):
            vector = _vector_from_columns(response, index)
            if vector is None:
                raise ValueError(f"missing online features for customer {customer_id}")
            output[int(customer_id)] = vector
        return output

    @property
    def source_sha256(self) -> str:
        if not self._source_sha256:
            raise RuntimeError("source hash is unavailable before prepare")
        return self._source_sha256

    @property
    def versions(self) -> dict[str, str]:
        return {
            "feast": version("feast"),
            "pandas": pd.__version__,
            "pyarrow": pyarrow.__version__,
        }

    def _write_config(self) -> None:
        config = """project: feature_store_lite
provider: local
registry: data/registry.db
online_store:
  type: sqlite
  path: data/online_store.db
entity_key_serialization_version: 3
"""
        (self.repo_path / "feature_store.yaml").write_text(
            config,
            encoding="utf-8",
            newline="\n",
        )
