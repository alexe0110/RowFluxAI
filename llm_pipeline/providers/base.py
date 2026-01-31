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
    async def transform(self, prompt: str, content: str) -> tuple[str, int, float]:
        """
        Transform content using the LLM.

        Args:
            prompt: System/instruction prompt.
            content: Content to transform.

        Returns:
            Tuple of (transformed_content, tokens_used, estimated_cost).
        """

    @abstractmethod
    async def validate_sql_match(
        self,
        select_query: str,
        update_query: str,
        validation_prompt: str,
    ) -> tuple[bool, str]:
        """
        Validate that SELECT and UPDATE queries work with the same field.

        Args:
            select_query: The SELECT query.
            update_query: The UPDATE query.
            validation_prompt: Prompt for the LLM to validate.

        Returns:
            Tuple of (is_valid, explanation).
        """
