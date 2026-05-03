from __future__ import annotations

import asyncio
import copy
from pathlib import Path
from typing import Any, Dict, cast

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

import main
from skill.assembler import assemble
from skill.constants import DEFAULT_MISTRAL_MODEL
from skill.retry_utils import call_with_retry
from skill.schema import PreAuthCaseInput


def _build_raw_eval() -> dict[str, object]:
    return {
        "recommendation": "LIKELY_APPROVE",
        "confidence": "HIGH",
        "clinical_summary": "Summary text.",
        "criteria_results": [
            {
                "criterion_id": "C1",
                "criterion_name": "Criterion one",
                "status": "MET",
                "supporting_evidence": "Evidence text.",
                "gap_or_risk": None,
            }
        ],
        "criteria_met": ["C1"],
        "criteria_partial_or_unmet": [],
        "supporting_evidence": [{"source": "Note", "excerpt": "Evidence text."}],
        "missing_information": [],
        "provider_query": "Should be cleared.",
        "appeal_direction": "Should be cleared.",
        "flip_condition": "Should be cleared.",
    }


def test_assemble_does_not_mutate_input() -> None:
    raw_eval = _build_raw_eval()
    original = copy.deepcopy(raw_eval)
    case_input = PreAuthCaseInput(
        case_id="PA-TEST",
        requested_service="Arthroplasty",
        primary_diagnosis="Osteoarthritis",
    )

    output = assemble(raw_eval, case_input, step1_ms=10, step2_ms=20, total_ms=30)

    assert raw_eval == original
    assert output.model_used == DEFAULT_MISTRAL_MODEL
    assert output.appeal_direction is None
    assert output.provider_query == ""
    assert output.flip_condition is None


@pytest.mark.asyncio
async def test_call_with_retry_does_not_retry_permanent_errors() -> None:
    calls = 0

    async def fail() -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError("401 unauthorized")

    with pytest.raises(RuntimeError):
        await call_with_retry(fail, max_retries=5)

    assert calls == 1


@pytest.mark.asyncio
async def test_call_with_retry_reuses_lock_within_same_loop() -> None:
    """
    Verify that call_with_retry works correctly for multiple calls within the same event loop.
    Since the global lock was removed, calls can now run concurrently.
    """
    call_count = 0
    
    async def track_calls() -> str:
        nonlocal call_count
        call_count += 1
        return "ok"
    
    # Make multiple calls within the same event loop
    result1 = await call_with_retry(track_calls)
    result2 = await call_with_retry(track_calls)
    
    assert result1 == "ok"
    assert result2 == "ok"
    assert call_count == 2


def test_call_with_retry_works_across_event_loops() -> None:
    """
    Verify that call_with_retry works correctly when called from separate event loops.
    Each asyncio.run() creates a new event loop, and the function should work correctly.
    """
    async def succeed() -> str:
        return "ok"

    # Each asyncio.run creates a new event loop, so this tests the basic functionality
    assert asyncio.run(call_with_retry(succeed)) == "ok"
    assert asyncio.run(call_with_retry(succeed)) == "ok"


@pytest.mark.parametrize(
    ("field_name", "kwargs"),
    [
        (
            "requested_service",
            {
                "requested_service": "x" * 501,
                "primary_diagnosis": "Valid diagnosis",
            },
        ),
        (
            "primary_diagnosis",
            {
                "requested_service": "Valid service",
                "primary_diagnosis": "x" * 501,
            },
        ),
    ],
)
def test_case_input_rejects_overlong_required_text(
    field_name: str, kwargs: Dict[str, object]
) -> None:
    with pytest.raises(ValidationError):
        PreAuthCaseInput(**cast(Any, kwargs))


def test_health_endpoint_does_not_expose_api_key_state() -> None:
    client = TestClient(main.app)

    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["model"] == DEFAULT_MISTRAL_MODEL
    assert "api_key_set" not in body


class _FailingUploadFile:
    def __init__(self) -> None:
        self.filename = "case.xlsx"
        self.closed = False

    async def read(self) -> bytes:
        raise RuntimeError("boom")

    async def close(self) -> None:
        self.closed = True


class _TempFileWrapper:
    def __init__(self, path: Path) -> None:
        self.name = str(path)
        self._handle = path.open("wb")

    def write(self, content: bytes) -> int:
        return self._handle.write(content)

    def __enter__(self) -> "_TempFileWrapper":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self._handle.close()


@pytest.mark.asyncio
async def test_analyze_upload_removes_temp_file_on_read_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    temp_file_path = tmp_path / "upload.xlsx"

    def fake_named_temporary_file(
        *args: object,
        **kwargs: object,
    ) -> _TempFileWrapper:
        return _TempFileWrapper(temp_file_path)

    monkeypatch.setattr(main.tempfile, "NamedTemporaryFile", fake_named_temporary_file)

    upload = _FailingUploadFile()

    with pytest.raises(RuntimeError):
        await main.analyze_upload(upload)  # type: ignore[arg-type]

    assert not temp_file_path.exists()
    assert upload.closed is True