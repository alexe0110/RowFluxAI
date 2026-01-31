import logging
from collections.abc import AsyncIterator

from llm_pipeline.models import ProcessingResult, Record
from llm_pipeline.providers.base import LLMProvider
from llm_pipeline.strategies.base import ProcessingStrategy
from llm_pipeline.utils.retry import with_retry
from llm_pipeline.validation.response_validator import validate_response

logger = logging.getLogger(__name__)


class SequentialStrategy(ProcessingStrategy):
    async def process(
        self,
        records: AsyncIterator[Record],
        provider: LLMProvider,
        prompt: str,
    ) -> AsyncIterator[ProcessingResult]:
        """Process records sequentially with retries."""
        async for record in records:
            yield await self._process_single(record, provider, prompt)

    @staticmethod
    async def _process_single(record: Record, provider: LLMProvider, prompt: str) -> ProcessingResult:
        """Process a single record with retry and validation."""
        try:
            transformed, tokens, cost = await with_retry(
                lambda: provider.transform(prompt, record.content)
            )

            is_valid, validation_error = validate_response(transformed)
            if not is_valid:
                logger.warning(f"Record {record.id}: validation failed - {validation_error}")
                return ProcessingResult(
                    record_id=record.id,
                    success=False,
                    original_content=record.content,
                    transformed_content=transformed,
                    tokens_used=tokens,
                    cost=cost,
                    error=f"Validation failed: {validation_error}",
                )

            return ProcessingResult(
                record_id=record.id,
                success=True,
                original_content=record.content,
                transformed_content=transformed,
                tokens_used=tokens,
                cost=cost,
            )

        except Exception as e:
            logger.error(f"Record {record.id}: failed - {e}")
            return ProcessingResult(
                record_id=record.id,
                success=False,
                original_content=record.content,
                error=str(e),
            )
