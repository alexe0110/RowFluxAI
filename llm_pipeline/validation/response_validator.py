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
        return False, f"Response too short (min {MIN_RESPONSE_LENGTH} chars)"

    if len(response) > MAX_RESPONSE_LENGTH:
        return False, f"Response too long (max {MAX_RESPONSE_LENGTH} chars)"

    if not validate_html_tags(response):
        return False, "Unclosed HTML tags detected"

    return True, None


def validate_html_tags(text: str) -> bool:
    """
    Simple HTML tag validation.

    Checks if opening and closing angle brackets are balanced.

    Args:
        text: Text to validate.

    Returns:
        True if tags appear balanced, False otherwise.
    """
    # todo: пока так, но надо сделать болле хитрую логику, эти символ могут встречатьс не только в html тэгах
    open_count = text.count("<")
    close_count = text.count(">")
    return open_count == close_count
