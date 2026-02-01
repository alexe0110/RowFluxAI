from abc import ABC, abstractmethod


class LLMProvider(ABC):
    def __init__(self, name: str, model: str, temperature: float = 0.7) -> None:
        """
        Initialize provider.

        Args:
            model: Model identifier.
            temperature: Sampling temperature.
        """
        self.name = name
        self.model = model
        self.temperature = temperature

    @abstractmethod
    async def execute(self, prompt: str, content: str) -> tuple[str, int, float]:
        """
        Execute request using the LLM.

        Args:
            prompt: System/instruction prompt.
            content: Content to transform.

        Returns:
            Tuple of (transformed_content, tokens_used, estimated_cost).
        """
