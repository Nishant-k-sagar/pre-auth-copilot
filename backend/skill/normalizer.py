"""
Step 1 of the pipeline: Normalization.

Calls Mistral once using complete_async() (non-blocking — mandatory for FastAPI).
Converts raw PreAuthCaseInput into a clean structured dict.
No clinical judgment is made here — only fact extraction.
"""

import json
import logging
from typing import Dict, cast

from mistralai import Mistral

from .constants import DEFAULT_MISTRAL_MODEL
from .errors import PipelineStepError
from .prompts import NORMALIZATION_SYSTEM_PROMPT, build_normalization_user_message
from .retry_utils import call_with_retry
from .schema import PreAuthCaseInput

logger = logging.getLogger(__name__)


async def normalize(case_input: PreAuthCaseInput, client: Mistral) -> Dict[str, object]:
    """
    Step 1: Normalize raw case input into a structured dict.

    Returns a plain dict (not a Pydantic model) because the evaluator
    needs flexibility to handle any field shape the LLM returns.
    The assembler handles final Pydantic validation.

    Uses complete_async() — not complete() — because FastAPI runs on an async
    event loop and synchronous I/O would block the entire server during the
    2-3 second Mistral round trip.
    """
    input_dict = cast(Dict[str, object], case_input.model_dump())
    user_message = build_normalization_user_message(input_dict)

    logger.debug("Normalization: user message length = %d chars", len(user_message))

    try:
        response = await call_with_retry(
            client.chat.complete_async,
            model=DEFAULT_MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": NORMALIZATION_SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.0,     # Deterministic — mandatory for medical reasoning
            max_tokens=3000,     # Complex outputs reach ~2500 tokens; 2000 risks truncation
            response_format={"type": "json_object"},  # Enforces JSON; no markdown fences
        )
    except Exception as e:
        logger.error("Mistral API error in normalization: %s", str(e))
        raise PipelineStepError(
            step="step1",
            message=f"Normalization step failed (Mistral API): {e}",
        ) from e

    if not response.choices or not response.choices[0].message:
        raise PipelineStepError(
            step="step1",
            message="Normalization step: Empty response from LLM",
        )

    content = response.choices[0].message.content  # type: ignore[union-attr,unknown-member,unknown-variable]
    if not isinstance(content, str):
        logger.error("Normalization: LLM returned non-string content")
        raise PipelineStepError(
            step="step1",
            message="Normalization step: LLM returned invalid content type",
            raw_llm_snippet=repr(content)[:300],
        )
    raw = content

    try:
        normalized = cast(Dict[str, object], json.loads(raw))
    except json.JSONDecodeError as e:
        logger.error("Normalization: invalid JSON from LLM: %s", raw[:500])
        raise PipelineStepError(
            step="step1",
            message="Normalization step: LLM returned invalid JSON.",
            raw_llm_snippet=raw[:300],
        ) from e

    logger.debug("Normalization complete.")
    return normalized
