import asyncio

from llm_pipeline import Pipeline, PostgresSink, PostgresSource
from llm_pipeline.config import AnthropicSettings, PGSettings
from llm_pipeline.providers.anthropic import AnthropicProvider


async def main() -> None:
    db_settings = PGSettings()
    anthropic_settings = AnthropicSettings()

    source = PostgresSource(
        query="SELECT id, step_content FROM step_info where step_type = 'THEORY' LIMIT 20",
        settings=db_settings,
        primary_key='id',
        content_field='step_content',
    )

    sink = PostgresSink(
        query='UPDATE step_info SET step_content = :content WHERE id = :id',
        settings=db_settings,
    )

    provider = AnthropicProvider(settings=anthropic_settings, model='claude-3-5-haiku-20241022')

    pipeline = Pipeline(
        source=source,
        sink=sink,
        provider=provider,
        prompt_file='prompts/add_conclusions.txt',
        validate_sql=True,
        batch_commit_size=10,
    )

    results = await pipeline.run()

    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    print(f'\nProcessed: {len(results)}, Success: {successful}, Failed: {failed}')


if __name__ == '__main__':
    asyncio.run(main())
