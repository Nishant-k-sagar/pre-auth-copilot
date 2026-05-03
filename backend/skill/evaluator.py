"""
Step 2 of the pipeline: Criteria Evaluation.

Calls Mistral once with the normalized case, service-appropriate criteria,
and 3 few-shot examples. Returns raw evaluation dict.

CRITICAL: Uses str.replace() for criteria injection — NOT .format().
str.replace() is safe if criteria descriptions contain { or } characters.
.format() would raise KeyError in that case.
"""

import json
import logging
from typing import Dict, List, Mapping, cast

from mistralai import Mistral

from .criteria_registry import Criterion, format_criteria_for_prompt
from .constants import DEFAULT_MISTRAL_MODEL
from .errors import PipelineStepError
from .prompts import EVALUATION_SYSTEM_PROMPT_TEMPLATE, build_evaluation_user_message
from .retry_utils import call_with_retry
from .schema import PreAuthCaseInput

logger = logging.getLogger(__name__)


async def evaluate(
    normalized_case: Mapping[str, object],
    criteria: List[Criterion],
    case_input: PreAuthCaseInput,
    client: Mistral,
) -> Dict[str, object]:
    """
    Step 2: Evaluate normalized case against service-appropriate criteria.
    Returns raw LLM JSON dict.
    """
    criteria_block = format_criteria_for_prompt(criteria)

    # str.replace() — safe with any criteria text content including { } characters
    system_prompt = EVALUATION_SYSTEM_PROMPT_TEMPLATE.replace(
        "{criteria_block}", criteria_block
    )

    user_message = build_evaluation_user_message(
        case_id=case_input.case_id or "unknown",
        requested_service=case_input.requested_service,
        site_of_care=case_input.site_of_care or "not specified",
        normalized_case=normalized_case,
    )

    logger.debug(
        "Evaluation: system=%d chars, user=%d chars",
        len(system_prompt), len(user_message)
    )

    try:
        response = await call_with_retry(
            client.chat.complete_async,
            model=DEFAULT_MISTRAL_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=0.0,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )
    except Exception as e:
        logger.error("Mistral API error in evaluation: %s", str(e))
        raise PipelineStepError(
            step="step2",
            message=f"Evaluation step failed (Mistral API): {e}",
        ) from e

    # Extract content with proper null checks
    if not response.choices or not response.choices[0].message:
        raise PipelineStepError(
            step="step2",
            message="Evaluation step: Empty response from LLM",
        )

    # Get content and validate it's a string (Mistral lib has incomplete type stubs)
    content = response.choices[0].message.content  # type: ignore[union-attr,unknown-member,unknown-variable]
    if not isinstance(content, str):
        logger.error("Evaluation: LLM returned non-string content")
        raise PipelineStepError(
            step="step2",
            message="Evaluation step: LLM returned invalid content type",
            raw_llm_snippet=repr(content)[:300],
        )
    raw = content

    try:
        result = cast(Dict[str, object], json.loads(raw))
    except json.JSONDecodeError as e:
        logger.error("Evaluation: invalid JSON from LLM: %s", raw[:500])
        raise PipelineStepError(
            step="step2",
            message="Evaluation step: LLM returned invalid JSON.",
            raw_llm_snippet=raw[:300],
        ) from e

    logger.debug(
        "Evaluation complete. recommendation=%s confidence=%s",
        result.get("recommendation"), result.get("confidence")
    )
    return result
