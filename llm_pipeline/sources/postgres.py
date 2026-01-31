from collections.abc import AsyncIterator

import asyncpg

from llm_pipeline.config import DatabaseSettings
from llm_pipeline.models import Record
from llm_pipeline.sources.base import DataSource


class PostgresSource(DataSource):
    def __init__(self, query: str, settings: DatabaseSettings, primary_key: str = "id", content_field: str = "content"):
        """
        Initialize pg source.

        Args:
            query: SELECT query to fetch records
            primary_key: Name of the primary key column.
            content_field: Name of the content column
            settings: Database settings. If None, loads from environment
        """
        self.query = query
        self.primary_key = primary_key
        self.content_field = content_field
        self._settings = settings
        self._pool: asyncpg.Pool | None = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(     # type: ignore[misc]
                host=self._settings.host,
                port=self._settings.port,
                database=self._settings.name,
                user=self._settings.user,
                password=self._settings.password,
                min_size=1, # Всегда держать 1 соединение открытым
                max_size=5, # Если нужно больше — создать 5, но не больше
            )
        return self._pool

    async def fetch_records(self) -> AsyncIterator[Record]:
        """Fetch records from PostgreSQL."""
        pool = await self._ensure_pool()

        async with pool.acquire() as conn:
            async with conn.transaction():
                async for row in conn.cursor(self.query):
                    row_dict = dict(row)
                    record_id = row_dict.pop(self.primary_key)
                    content = row_dict.pop(self.content_field)
                    yield Record(id=record_id,content=content,metadata=row_dict)

    async def count_records(self) -> int:
        """Count total records matching the query."""
        pool = await self._ensure_pool()

        count_query = f"SELECT COUNT(*) FROM ({self.query}) AS subquery"
        async with pool.acquire() as conn:
            result = await conn.fetchval(count_query)
            return result or 0

    async def close(self) -> None:
        """Close pool"""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def get_query(self) -> str:
        return self.query
