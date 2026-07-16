from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from feature_store_lite.domain import FeatureRecord, FeatureVector, HistoricalQuery


class FeatureStorePort(Protocol):
    def prepare(self, records: Sequence[FeatureRecord]) -> None: ...

    def historical(
        self,
        queries: Sequence[HistoricalQuery],
    ) -> Mapping[str, FeatureVector | None]: ...

    def materialize(self, start, end) -> float: ...

    def start_online_session(self) -> None: ...

    def online(self, customer_ids: Sequence[int]) -> Mapping[int, FeatureVector]: ...

    @property
    def source_sha256(self) -> str: ...

    @property
    def versions(self) -> Mapping[str, str]: ...
