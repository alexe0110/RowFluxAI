from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from llm_pipeline.config import OpenAISettings
from llm_pipeline.providers.base import LLMProvider

PRICING = {
    'gpt-4': {'input': 0.03, 'output': 0.06},
    'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
    'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
    'gpt-4o': {'input': 0.005, 'output': 0.015},
    'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
    'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
}


class OpenAIProvider(LLMProvider):
    def __init__(self, settings: OpenAISettings, model: str = 'gpt-4o', temperature: float = 0.7) -> None:
        """
        Initialize OpenAI provider.

        Args:
            model: OpenAI model to use.
            temperature: Sampling temperature.
            settings: OpenAI settings. If None, loads from environment.
        """
        super().__init__('OpenAI', model, temperature)
        self._settings = settings
        self._client = AsyncOpenAI(api_key=self._settings.api_key)

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token usage."""

        pricing = PRICING.get(self.model, {'input': 0.01, 'output': 0.03})
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return input_cost + output_cost

    async def transform(self, prompt: str, content: str) -> tuple[str, int, float]:
        """Transform content using OpenAI."""
        response = await self._client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                ChatCompletionSystemMessageParam(role='system', content=prompt),
                ChatCompletionUserMessageParam(role='user', content=content),
            ],
        )

        result = response.choices[0].message.content or ''
        usage = response.usage

        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
        total_tokens = input_tokens + output_tokens
        cost = self._calculate_cost(input_tokens, output_tokens)

        return result, total_tokens, cost

    async def validate_sql_match(
        self,
        select_query: str,
        update_query: str,
        validation_prompt: str,
    ) -> tuple[bool, str]:
        """Validate SQL queries match using OpenAI."""
        # todo: пока костыль, нужно норм вынести промпт + мб что то в абстракттый класс
        full_prompt = f"""{validation_prompt}

SELECT query:
{select_query}

UPDATE query:
{update_query}

Answer with "VALID" if the queries work with the same field, or "INVALID: <reason>" if not."""

        response = await self._client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                ChatCompletionUserMessageParam(role='user', content=full_prompt),
            ],
        )

        result = response.choices[0].message.content or ''
        is_valid = result.strip().upper().startswith('VALID')
        return is_valid, result.strip()
