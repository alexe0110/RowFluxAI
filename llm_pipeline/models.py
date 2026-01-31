from typing import Any

from pydantic import BaseModel, Field


class Record(BaseModel):
    """A single record from the database to be processed."""

    id: Any
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessingResult(BaseModel):
    """Result of processing a single record through the LLM."""

    record_id: Any
    success: bool
    original_content: str
    transformed_content: str | None = None
    tokens_used: int = 0
    cost: float = 0.0
    error: str | None = None
