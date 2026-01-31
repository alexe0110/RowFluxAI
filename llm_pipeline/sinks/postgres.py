import re
from typing import Any

import asyncpg

from llm_pipeline.config import DatabaseSettings
from llm_pipeline.sinks.base import DataSink


class PostgresSink(DataSink):
    def __init__(self, query: str, settings: DatabaseSettings):
        """
        Initialize PostgreSQL sink.

        Args:
            query: UPDATE query with :content and :id placeholders.
                Example: "UPDATE table SET content = :content WHERE id = :id"
            settings: Database connection settings.
        """
        self.query = query
        self._settings = settings
        self._pool: asyncpg.Pool | None = None
        self._pending: list[tuple[Any, str]] = []
        self._prepared_query, self._param_order = self._convert_query(query)

    @staticmethod
    def _convert_query(query: str) -> tuple[str, list[str]]:
        pattern = re.compile(r":(\w+)")
        placeholders = pattern.findall(query)

        result = query
        for i, name in enumerate(placeholders, 1):
            result = result.replace(f":{name}", f"${i}", 1)

        return result, placeholders

    async def _ensure_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            self._pool = await asyncpg.create_pool(  # type: ignore[misc]
                host=self._settings.host,
                port=self._settings.port,
                database=self._settings.name,
                user=self._settings.user,
                password=self._settings.password,
                min_size=1,
                max_size=5,
            )
        return self._pool

    def _build_params(self, record_id: Any, content: str) -> list[Any]:
        params = []
        for name in self._param_order:
            if name == "content":
                params.append(content)
            elif name == "id":
                params.append(record_id)
            else:
                raise ValueError(f"Unknown placeholder: {name}")
        return params

    async def write_record(self, record_id: Any, content: str) -> None:
        """
        Buffer record for batch write

        Args:
            record_id: The primary key of the record.
            content: The transformed content.
        """
        self._pending.append((record_id, content))

    async def commit_batch(self) -> None:
        if not self._pending:
            return

        pool = await self._ensure_pool()
        args = [self._build_params(rid, content) for rid, content in self._pending]

        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.executemany(self._prepared_query, args)

        self._pending.clear()

    async def close(self) -> None:
        await self.commit_batch()
        if self._pool is not None:
            await self._pool.close()
            self._pool = None

    def get_query(self) -> str:
        return self.query

    @property
    def pending_count(self) -> int:
        return len(self._pending)
