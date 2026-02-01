import asyncio

from llm_pipeline import Pipeline, PostgresSink, PostgresSource
from llm_pipeline.config import OpenAISettings, PGSettings
from llm_pipeline.providers import OpenAIProvider


async def main() -> None:
    db_settings = PGSettings()
    openai_settings = OpenAISettings()

    source = PostgresSource(
        query="SELECT id, step_content FROM table1 where step_type = 'THEORY' LIMIT 5",
        settings=db_settings,
        primary_key='id',
        content_field='step_content',
    )

    sink = PostgresSink(
        query='UPDATE table1 SET step_content = :content WHERE id = :id',
        settings=db_settings,
    )

    provider = OpenAIProvider(settings=openai_settings)

    pipeline = Pipeline(
        source=source,
        sink=sink,
        provider=provider,
        prompt_file='prompts/add_conclusions.txt',
        validate_sql=True,
        batch_commit_size=10,
    )

    results = await pipeline.run()
    if not results:
        return
    successful = sum(1 for r in results if r.success)
    failed = len(results) - successful
    print(f'\nProcessed: {len(results)}, Success: {successful}, Failed: {failed}')


if __name__ == '__main__':
    asyncio.run(main())
