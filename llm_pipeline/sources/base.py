from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from llm_pipeline.models import Record


class DataSource(ABC):
    @abstractmethod
    def fetch_records(self) -> AsyncGenerator[Record]:
        """Yield records for processing."""

    @abstractmethod
    async def count_records(self) -> int:
        """Return total number of records to process."""

    @abstractmethod
    async def close(self) -> None:
        """Close the data source connection."""
