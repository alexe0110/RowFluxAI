from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from llm_pipeline.models import ProcessingResult, Record
from llm_pipeline.providers.base import LLMProvider


class ProcessingStrategy(ABC):
    @abstractmethod
    async def process(
        self,
        records: AsyncIterator[Record],
        provider: LLMProvider,
        prompt: str,
    ) -> AsyncIterator[ProcessingResult]:
        """
        Process records through the LLM.

        Args:
            records: Async iterator of records to process.
            provider: LLM provider to use.
            prompt: Prompt template for transformation.

        Yields:
            ProcessingResult for each processed record.
        """
        pass
