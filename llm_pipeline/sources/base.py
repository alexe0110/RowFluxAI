from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from llm_pipeline.models import Record


class DataSource(ABC):
    @abstractmethod
    async def fetch_records(self) -> AsyncIterator[Record]:
        """Yield records for processing."""
        pass

    @abstractmethod
    async def count_records(self) -> int:
        """Return total number of records to process."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close the data source connection."""
        pass
