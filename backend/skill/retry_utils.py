import asyncio
import logging
import random
from typing import Awaitable, Callable, Optional, TypeVar

import httpx
from mistralai.models import SDKError
from typing_extensions import ParamSpec

logger = logging.getLogger(__name__)

T = TypeVar("T")
P = ParamSpec("P")

_RETRIABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_PERMANENT_ERROR_MARKERS = (
    "400",
    "401",
    "403",
    "404",
    "422",
    "bad request",
    "invalid api key",
    "invalid_request",
    "authentication",
    "unauthorized",
    "forbidden",
)


def _get_exception_status_code(exception: Exception) -> Optional[int]:
    if isinstance(exception, SDKError):
        return exception.status_code

    response = getattr(exception, "response", None)
    if response is not None:
        status_code = getattr(response, "status_code", None)
        if isinstance(status_code, int):
            return status_code

    return None


def _retry_delay_from_exception(exception: Exception) -> Optional[float]:
    if isinstance(exception, SDKError) and exception.raw_response is not None:
        retry_after = exception.raw_response.headers.get("retry-after")
        if retry_after:
            try:
                return max(float(retry_after), 0.0)
            except ValueError:
                return None
    return None


def _is_retriable_exception(exception: Exception) -> bool:
    status_code = _get_exception_status_code(exception)
    if status_code is not None:
        if status_code in _RETRIABLE_STATUS_CODES:
            return True
        if 400 <= status_code < 500:
            return False

    if isinstance(exception, (httpx.ConnectError, httpx.TimeoutException, asyncio.TimeoutError)):
        return True

    message = str(exception).lower()
    if any(marker in message for marker in _PERMANENT_ERROR_MARKERS):
        return False

    return any(
        marker in message
        for marker in (
            "429",
            "too many requests",
            "rate limit",
            "temporary failure",
            "event loop is closed",
        )
    )

async def call_with_retry(
    func: Callable[P, Awaitable[T]],
    max_retries: int = 5,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    *args: P.args,
    **kwargs: P.kwargs,
) -> T:
    """
    Executes an async function with exponential backoff.

    Note: This function does not serialize calls globally. For rate limit protection,
    use a semaphore at the caller level if needed.
    """
    delay = initial_delay
    last_exception: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if not _is_retriable_exception(e):
                raise

            if attempt == max_retries:
                raise

            retry_after = _retry_delay_from_exception(e)
            sleep_for = retry_after if retry_after is not None else delay
            sleep_for = max(sleep_for + random.uniform(0.0, 0.25), 0.0)

            logger.warning(
                "API call failed on attempt %d/%d. Exception: %s. Retrying in %.1f seconds...",
                attempt,
                max_retries,
                str(e),
                sleep_for,
            )

            await asyncio.sleep(sleep_for)
            delay *= backoff_factor

    raise RuntimeError(f"Failed after {max_retries} attempts. Last error: {last_exception}") from last_exception