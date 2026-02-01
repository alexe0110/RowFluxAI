import asyncio
import logging
import signal
import time
from pathlib import Path

from rich.console import Console

from llm_pipeline.models import ProcessingResult
from llm_pipeline.providers.base import LLMProvider
from llm_pipeline.sinks.base import DataSink
from llm_pipeline.sources.base import DataSource
from llm_pipeline.strategies.base import ProcessingStrategy
from llm_pipeline.strategies.sequential import SequentialStrategy
from llm_pipeline.utils.logging import setup_logging
from llm_pipeline.utils.progress import ProgressTracker
from llm_pipeline.utils.retry import with_retry
from llm_pipeline.validation.sql_validator import validate_sql_queries

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(
        self,
        source: DataSource,
        sink: DataSink,
        provider: LLMProvider,
        prompt_file: str | Path,
        strategy: ProcessingStrategy | None = None,
        validate_sql: bool = True,
        batch_commit_size: int = 10,
        sql_validation_prompt_file: str | Path | None = None,
    ) -> None:
        """
        Initialize the pipeline.

        Args:
            source: Data source to read records from.
            sink: Data sink to write results to.
            provider: LLM provider for transformation.
            prompt_file: Path to the prompt file.
            strategy: Processing strategy. Defaults to SequentialStrategy.
            validate_sql: Whether to validate SQL queries before processing.
            batch_commit_size: Number of records before committing a batch.
            sql_validation_prompt_file: Optional path to SQL validation prompt.
        """
        self.source = source
        self.sink = sink
        self.provider = provider
        self.prompt_file = Path(prompt_file)
        self.strategy = strategy or SequentialStrategy()
        self.validate_sql = validate_sql
        self.batch_commit_size = batch_commit_size
        self.sql_validation_prompt_file = sql_validation_prompt_file

        self._shutdown_event = asyncio.Event()
        self.console = Console()
        self.results: list[ProcessingResult] = []

    def _load_prompt(self) -> str:
        if not self.prompt_file.exists():
            raise FileNotFoundError(f'Prompt file not found: {self.prompt_file}')
        return self.prompt_file.read_text(encoding='utf-8').strip()

    def _setup_signal_handlers(self) -> None:
        """Setup graceful shutdown handlers."""
        loop = asyncio.get_running_loop()

        def handle_shutdown(sig: signal.Signals) -> None:
            logger.warning('Received %s, initiating graceful shutdown...', sig.name)
            self._shutdown_event.set()

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_shutdown, sig)

    async def _validate_sql_queries(self) -> bool:
        """Validate that SELECT and UPDATE queries are compatible."""
        if not hasattr(self.source, 'get_query') or not hasattr(self.sink, 'get_query'):
            logger.warning('Source or sink does not expose query - skipping SQL validation')
            return True

        select_query = self.source.get_query()
        update_query = self.sink.get_query()

        logger.info('Validating SQL query compatibility...')

        try:
            is_valid, explanation = await with_retry(
                lambda: validate_sql_queries(
                    provider=self.provider,
                    select_query=select_query,
                    update_query=update_query,
                    prompt_file=self.sql_validation_prompt_file,
                )
            )

            if is_valid:
                logger.info('SQL validation passed')
            else:
                logger.error('SQL validation failed: %s', explanation)

            return is_valid

        except Exception:
            return False

    async def run(self) -> list[ProcessingResult] | None:
        """Run the pipeline."""

        setup_logging()

        logger.info('Starting pipeline with provider: %s', self.provider.name)
        logger.info('Model: %s', self.provider.model)

        if self.validate_sql:
            is_valid = await self._validate_sql_queries()
            if not is_valid:
                return None

        prompt = self._load_prompt()
        logger.info('Loaded prompt from: %s', self.prompt_file)

        self._setup_signal_handlers()

        total_records = await self.source.count_records()
        logger.info('Total records to process: %s', total_records)

        if total_records == 0:
            logger.warning('No records to process')
            return []

        start_time = time.monotonic()
        records_processed = 0

        try:
            with ProgressTracker(total_records, self.console) as progress:
                async for result in self.strategy.process(
                    self.source.fetch_records(),
                    self.provider,
                    prompt,
                ):
                    if self._shutdown_event.is_set():
                        logger.warning('Shutdown requested, finishing current batch...')
                        break

                    self.results.append(result)
                    records_processed += 1

                    if result.success and result.transformed_content:
                        await self.sink.write_record(result.record_id, result.transformed_content)

                    progress.update(success=result.success, tokens=result.tokens_used, cost=result.cost)

                    if records_processed % self.batch_commit_size == 0:
                        await self.sink.commit_batch()
                        logger.debug('Committed batch at record %s', records_processed)

                await self.sink.commit_batch()

                duration = time.monotonic() - start_time
                progress.print_summary(duration)

        except Exception as e:
            logger.error('Pipeline error: %s', e)
            raise
        finally:
            await self.source.close()
            await self.sink.close()

        return self.results
