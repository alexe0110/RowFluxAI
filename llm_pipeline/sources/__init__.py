"""Data sources for the LLM pipeline."""

from .base import DataSource
from .postgres import PostgresSource

__all__ = ["DataSource", "PostgresSource"]
