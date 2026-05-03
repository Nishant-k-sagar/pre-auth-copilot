"""Shared skill-layer exception types."""

from typing import Optional


class PipelineStepError(RuntimeError):
    """Raised when a specific pipeline step fails with structured context."""

    def __init__(
        self,
        step: str,
        message: str,
        raw_llm_snippet: Optional[str] = None,
    ) -> None:
        self.step = step
        self.message = message
        self.raw_llm_snippet = raw_llm_snippet
        super().__init__(message)
