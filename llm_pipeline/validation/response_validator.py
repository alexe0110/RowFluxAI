MIN_RESPONSE_LENGTH = 10
MAX_RESPONSE_LENGTH = 50000


def validate_response(response: str) -> tuple[bool, str | None]:
    """
    Validate LLM response

    Args:
        response: The LLM response to validate.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is None.
    """
    if not response or len(response.strip()) < MIN_RESPONSE_LENGTH:
        return False, f'Response too short (min {MIN_RESPONSE_LENGTH} chars)'

    if len(response) > MAX_RESPONSE_LENGTH:
        return False, f'Response too long (max {MAX_RESPONSE_LENGTH} chars)'

    return True, None
