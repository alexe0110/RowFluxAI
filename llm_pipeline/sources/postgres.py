from collections.abc import AsyncGenerator

import asyncpg

from llm_pipeline.config import PGSettings
from llm_pipeline.models import Record
from llm_pipeline.sources.base import DataSource


class PostgresSource(DataSource):
    def __init__(
        self, query: str, settings: PGSettings, primary_key: str = 'id', content_field: str = 'content'
    ) -> None:
        """
        Initialize pg source.

        Args:
            query: SELECT query to fetch records.
            settings: Database connection settings.
            primary_key: Name of the primary key column.
            content_field: Name of the content column.
        """
        self.query = query
        self.primary_key = primary_key
        self.content_field = content_field
        self._settings = settings
        self._pool: asyncpg.Pool | None = None

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(  # type: ignore[misc]
                host=self._settings.host,
                port=self._settings.port,
                database=self._settings.db,
                user=self._settings.user,
                password=self._settings.password.get_secret_value(),
                min_size=1,
                max_size=5,
            )
        return self._pool

    async def fetch_records(self) -> AsyncGenerator[Record]:
        """Fetch records from PostgreSQL."""
        pool = await self._ensure_pool()

        async with pool.acquire() as conn, conn.transaction():
            async for row in conn.cursor(self.query):
                row_dict = dict(row)
                record_id = row_dict.pop(self.primary_key)
                content = row_dict.pop(self.content_field)
                yield Record(id=record_id, content=content, metadata=row_dict)

    async def count_records(self) -> int:
        """Count total records matching the query."""
        pool = await self._ensure_pool()

        count_query = f'SELECT COUNT(*) FROM ({self.query}) AS subquery'  # noqa: S608
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
