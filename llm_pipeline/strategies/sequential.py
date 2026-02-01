import logging
from collections.abc import AsyncGenerator

from llm_pipeline.models import ProcessingResult, Record
from llm_pipeline.providers.base import LLMProvider
from llm_pipeline.strategies.base import ProcessingStrategy
from llm_pipeline.utils.retry import with_retry
from llm_pipeline.validation.response_validator import validate_response

logger = logging.getLogger(__name__)


class SequentialStrategy(ProcessingStrategy):
    async def process(
        self,
        records: AsyncGenerator[Record],
        provider: LLMProvider,
        prompt: str,
    ) -> AsyncGenerator[ProcessingResult]:
        """Process records sequentially with retries."""
        async for record in records:
            yield await self._process_single(record, provider, prompt)

    @staticmethod
    async def _process_single(record: Record, provider: LLMProvider, prompt: str) -> ProcessingResult:
        """Process a single record with retry and validation."""
        try:
            transformed, tokens, cost = await with_retry(lambda: provider.execute(prompt, record.content))

            is_valid, validation_error = validate_response(transformed)
            if not is_valid:
                logger.warning('Record %s: validation failed - %s', record.id, validation_error)
                return ProcessingResult(
                    record_id=record.id,
                    success=False,
                    original_content=record.content,
                    transformed_content=transformed,
                    tokens_used=tokens,
                    cost=cost,
                    error=f'Validation failed: {validation_error}',
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
            logger.error('Record %s: failed - %s', record.id, e)
            return ProcessingResult(
                record_id=record.id,
                success=False,
                original_content=record.content,
                error=str(e),
            )
