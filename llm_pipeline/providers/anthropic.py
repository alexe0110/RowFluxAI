from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from llm_pipeline.config import AnthropicSettings
from llm_pipeline.providers.base import LLMProvider

PRICING = {
    # https://platform.claude.com/docs/en/about-claude/pricing
    'claude-opus-4-5': {'input': 0.005, 'output': 0.025},
    'claude-sonnet-4-5': {'input': 0.003, 'output': 0.015},
    'claude-haiku-4-5': {'input': 0.001, 'output': 0.005},
}


class AnthropicProvider(LLMProvider):
    def __init__(
        self,
        settings: AnthropicSettings,
        model: str = 'claude-sonnet-4-5-20251101',
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        """
        Initialize Anthropic provider

        Args:
            model: Anthropic model to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            settings: Anthropic settings. If None, loads from environment
        """
        super().__init__('Anthropic', model, temperature)
        self.max_tokens = max_tokens
        self._settings = settings
        self._client = AsyncAnthropic(api_key=self._settings.anthropic_api_key)

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token usage."""
        pricing = PRICING.get(self.model, {'input': 0.003, 'output': 0.015})
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return input_cost + output_cost

    async def transform(self, prompt: str, content: str) -> tuple[str, int, float]:
        """Transform content using Anthropic"""
        response = await self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=prompt,
            messages=[
                MessageParam(role='user', content=content),
            ],
        )

        result = ''
        for block in response.content:
            if block.type == 'text':
                result += block.text

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        total_tokens = input_tokens + output_tokens
        cost = self._calculate_cost(input_tokens, output_tokens)

        return result, total_tokens, cost

    async def validate_sql_match(
        self,
        select_query: str,
        update_query: str,
        validation_prompt: str,
    ) -> tuple[bool, str]:
        """Validate SQL queries match using Anthropic"""
        # todo: тоже поправить
        full_prompt = f"""{validation_prompt}

SELECT query:
{select_query}

UPDATE query:
{update_query}

Answer with "VALID" if the queries work with the same field, or "INVALID: <reason>" if not."""

        response = await self._client.messages.create(
            model=self.model,
            max_tokens=500,
            temperature=0,
            messages=[
                MessageParam(role='user', content=full_prompt),
            ],
        )

        result = ''
        for block in response.content:
            if block.type == 'text':
                result += block.text

        is_valid = result.strip().upper().startswith('VALID')
        return is_valid, result.strip()
