import httpx

from llm_pipeline.config import YandexSettings
from llm_pipeline.providers.base import LLMProvider

PRICING = {
    'yandexgpt': {'input': 0.0002, 'output': 0.0004},
    'yandexgpt-lite': {'input': 0.00004, 'output': 0.00008},
}


class YandexProvider(LLMProvider):
    API_URL = 'https://llm.api.cloud.yandex.net/foundationModels/v1/completion'

    def __init__(
        self,
        settings: YandexSettings,
        model: str = 'yandexgpt',
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> None:
        """
        Initialize YandexGPT provider.

        Args:
            model: YandexGPT model to use.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            settings: Yandex settings. If None, loads from environment.
        """
        super().__init__('Yandex', model, temperature)
        self.max_tokens = max_tokens
        self._settings = settings

    def _get_model_uri(self) -> str:
        """Get full model URI for Yandex API."""
        return f'gpt://{self._settings.yandex_folder_id}/{self.model}/latest'

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost based on token usage."""
        pricing = PRICING.get(self.model, {'input': 0.0002, 'output': 0.0004})
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return input_cost + output_cost

    async def execute(self, prompt: str, content: str) -> tuple[str, int, float]:
        """Transform content using YandexGPT."""
        headers = {
            'Authorization': f'Api-Key {self._settings.yandex_api_key}',
            'Content-Type': 'application/json',
        }

        payload = {
            'modelUri': self._get_model_uri(),
            'completionOptions': {
                'stream': False,
                'temperature': self.temperature,
                'maxTokens': str(self.max_tokens),
            },
            'messages': [
                {'role': 'system', 'text': prompt},
                {'role': 'user', 'text': content},
            ],
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(self.API_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()

        result_data = data.get('result', {})
        alternatives = result_data.get('alternatives', [])

        result = alternatives[0].get('message', {}).get('text', '') if alternatives else ''

        usage = result_data.get('usage', {})
        input_tokens = int(usage.get('inputTextTokens', 0))
        output_tokens = int(usage.get('completionTokens', 0))
        total_tokens = input_tokens + output_tokens
        cost = self._calculate_cost(input_tokens, output_tokens)

        return result, total_tokens, cost
