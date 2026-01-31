from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from llm_pipeline.models import ProcessingResult, Record
from llm_pipeline.providers.base import LLMProvider


class ProcessingStrategy(ABC):
    @abstractmethod
    def process(
        self,
        records: AsyncGenerator[Record],
        provider: LLMProvider,
        prompt: str,
    ) -> AsyncGenerator[ProcessingResult]:
        """
        Process records through the LLM.

        Args:
            records: Async generator of records to process.
            provider: LLM provider to use.
            prompt: Prompt template for transformation.

        Yields:
            ProcessingResult for each processed record.
        """
