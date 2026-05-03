"""
Pipeline orchestrator.

Chains: normalize → evaluate → assemble, with timing instrumentation.

LAZY CLIENT SINGLETON:
    The Mistral client is initialized on first call, not at module import time.

    WHY: Module-level init (e.g., _client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY", "")))
    executes before load_dotenv() if any file imports pipeline before calling dotenv.
    Result: client gets an empty-string key, no error at import, silent auth failure
    6 seconds into the first API call.

    The lazy singleton raises RuntimeError immediately with a clear message
    if MISTRAL_API_KEY is missing when the pipeline is first called.
"""

import logging
import os
import time
from typing import Optional

from mistralai import Mistral
from mistralai.utils import BackoffStrategy, RetryConfig

from .assembler import assemble
from .criteria_registry import get_criteria
from .evaluator import evaluate
from .normalizer import normalize
from .schema import PreAuthCaseInput, PreAuthSkillOutput

logger = logging.getLogger(__name__)

# Use a module-level lock for thread-safe lazy initialization.
# The lock is acquired before checking and setting the client, ensuring
# proper memory visibility across threads.
import threading as _threading
_client: Optional[Mistral] = None
_client_lock = _threading.Lock()


def _build_retry_config() -> RetryConfig:
    """Return the SDK retry policy used for chat completion requests."""
    return RetryConfig(
        strategy="backoff",
        backoff=BackoffStrategy(
            initial_interval=1000,
            max_interval=30000,
            exponent=2.0,
            max_elapsed_time=120000,
        ),
        retry_connection_errors=True,
    )


def _get_client() -> Mistral:
    """
    Lazy singleton. Initializes the Mistral client on first call.
    Raises RuntimeError with a clear message if MISTRAL_API_KEY is not set.
    
    Thread-safe: Uses a lock to ensure only one client is created and
    properly published to all threads.
    """
    global _client
    # Fast path: client already initialized
    if _client is not None:
        return _client
    
    # Slow path: acquire lock and initialize
    with _client_lock:
        # Double-check after acquiring lock
        if _client is None:
            api_key = os.environ.get("MISTRAL_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "MISTRAL_API_KEY is not set. "
                    "Ensure load_dotenv() is called before the pipeline is used, "
                    "or set the environment variable directly."
                )
            _client = Mistral(api_key=api_key, retry_config=_build_retry_config())
            logger.info("Mistral client initialized.")
    return _client


async def run_pipeline(case_input: PreAuthCaseInput) -> PreAuthSkillOutput:
    """
    Full 3-step pipeline with timing.
    Step 1: Normalize  (Mistral call #1)
    Step 2: Evaluate   (Mistral call #2, service-appropriate criteria)
    Step 3: Assemble   (Python only, Pydantic validation)
    """
    client = _get_client()
    t0 = time.monotonic()

    # Step 1
    logger.info("Step 1: Normalizing case '%s'", case_input.case_id)
    t1 = time.monotonic()
    normalized = await normalize(case_input, client)
    step1_ms = int((time.monotonic() - t1) * 1000)
    logger.info("Step 1 complete: %dms", step1_ms)

    # Step 2
    criteria = get_criteria(case_input.requested_service)
    logger.info("Step 2: Evaluating with %d criteria for '%s'", len(criteria), case_input.requested_service)
    t2 = time.monotonic()
    raw_eval = await evaluate(normalized, criteria, case_input, client)
    step2_ms = int((time.monotonic() - t2) * 1000)
    logger.info("Step 2 complete: %dms | recommendation=%s", step2_ms, raw_eval.get("recommendation"))

    # Step 3
    total_ms = int((time.monotonic() - t0) * 1000)
    logger.info("Step 3: Assembling output. Total so far: %dms", total_ms)
    output = assemble(raw_eval, case_input, step1_ms, step2_ms, total_ms)

    logger.info(
        "Pipeline complete | case=%s | recommendation=%s | confidence=%s | total=%dms",
        output.case_id, output.recommendation, output.confidence, output.processing_time_ms
    )
    return output