import logging
from collections.abc import Awaitable, Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
WAIT_MIN = 4
WAIT_MAX = 60
WAIT_MULTIPLIER = 4


class RetryableError(Exception): """Base class for errors that should trigger retry."""


class RateLimitError(RetryableError): """Rate limit exceeded error."""


class TimeoutError(RetryableError): """Request timeout error."""


def _before_sleep(retry_state) -> None:
    attempt = retry_state.attempt_number
    wait = retry_state.next_action.sleep if retry_state.next_action else 0
    exc = retry_state.outcome.exception() if retry_state.outcome else None
    logger.warning(
        f"Retry attempt {attempt}/{MAX_ATTEMPTS} after error: {exc}. "
        f"Waiting {wait:.1f}s before next attempt."
    )

async def with_retry[T](func: Callable[[], Awaitable[T]]) -> T:
    """
    Execute an async function with retry logic.

    Args:
        func: Async function to execute.

    Returns:
        Result of the function.

    Raises:
        Exception: The last exception if all retries fail.
    """

    @retry(
        retry=retry_if_exception_type(RetryableError),
        stop=stop_after_attempt(MAX_ATTEMPTS),
        wait=wait_exponential(multiplier=WAIT_MULTIPLIER, min=WAIT_MIN, max=WAIT_MAX),
        before_sleep=_before_sleep,
        reraise=True,
    )
    async def wrapped() -> T:
        try:
            return await func()
        except Exception as e:
            error_name = type(e).__name__.lower()
            error_str = str(e).lower()

            if "rate" in error_name or "rate" in error_str or "429" in error_str:
                raise RateLimitError(str(e)) from e
            if "timeout" in error_name or "timeout" in error_str:
                raise TimeoutError(str(e)) from e

            raise

    return await wrapped()
