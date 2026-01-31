from pathlib import Path

from ..providers.base import LLMProvider

DEFAULT_VALIDATION_PROMPT = """\
You are a SQL expert. Your task is to verify that a SELECT query \
and an UPDATE query work with the same database field.

The SELECT query should read data from a field, and the UPDATE query \
should write transformed data back to the same field.

Analyze the queries and determine if they are compatible - i.e., \
the field being read in SELECT is the same field being updated in UPDATE."""


async def validate_sql_queries(
    provider: LLMProvider,
    select_query: str,
    update_query: str,
    prompt_file: str | Path | None = None,
) -> tuple[bool, str]:
    """
    Validate that SELECT and UPDATE queries work with the same field.

    Args:
        provider: LLM provider to use for validation.
        select_query: The SELECT query.
        update_query: The UPDATE query.
        prompt_file: Optional path to custom validation prompt file.

    Returns:
        Tuple of (is_valid, explanation).
    """
    if prompt_file:
        prompt_path = Path(prompt_file)
        if prompt_path.exists():
            validation_prompt = prompt_path.read_text(encoding="utf-8")
        else:
            validation_prompt = DEFAULT_VALIDATION_PROMPT
    else:
        validation_prompt = DEFAULT_VALIDATION_PROMPT

    return await provider.validate_sql_match(select_query, update_query, validation_prompt)
