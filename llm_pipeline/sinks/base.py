from abc import ABC, abstractmethod
from typing import Any


class DataSink(ABC):
    @abstractmethod
    async def write_record(self, record_id: Any, content: str) -> None:
        """
        Write a single transformed record.

        Args:
            record_id: The primary key of the record.
            content: The transformed content.
        """

    @abstractmethod
    async def commit_batch(self) -> None:
        """Commit the current batch of records."""

    @abstractmethod
    async def close(self) -> None:
        """Close the sink connection."""
