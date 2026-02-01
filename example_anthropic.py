import asyncio

from llm_pipeline import Pipeline, PostgresSink, PostgresSource
from llm_pipeline.config import AnthropicSettings, PGSettings
from llm_pipeline.providers.anthropic import AnthropicProvider


async def main() -> None:
    db_settings = PGSettings()
    anthropic_settings = AnthropicSettings()

    source_query = """
    select si.id, si.step_content
from table1 si
inner join table2 lsi on si.id = lsi.step_id
where lsi.lesson_id = '3d6123f6-3124-4d7e-b006-7094e2483522' and si.step_type = 'TEST' limit 20"""

    source = PostgresSource(
        query=source_query,
        settings=db_settings,
        primary_key='id',
        content_field='step_content',
    )

    sink = PostgresSink(
        query='UPDATE table1 SET step_content = :content WHERE id = :id',
        settings=db_settings,
    )

    provider = AnthropicProvider(settings=anthropic_settings, model='claude-3-5-haiku-20241022')

    pipeline = Pipeline(
        source=source,
        sink=sink,
        provider=provider,
        prompt_file='prompts/convert_task_to_json.txt',
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
