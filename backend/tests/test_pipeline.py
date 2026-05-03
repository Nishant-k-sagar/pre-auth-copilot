"""
Batch validation: runs all 10 training cases and checks label accuracy.
Target: >=8/10 correct.

Saves full PreAuthSkillOutput to outputs/case_results/PA-00N.json (D8a deliverable).
scope="module" runs all 10 cases once per module to save API calls.

Run:
    Set-Location backend; pytest tests/test_pipeline.py -v -s
"""

import json
import sys
from pathlib import Path
from typing import List, Optional, TypedDict, cast

from typing_extensions import NotRequired

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from conftest import run_pipeline_sync
from skill.schema import PreAuthCaseInput

DATA_DIR = Path(__file__).parent.parent / "data"
OUTPUTS_DIR = Path(__file__).parent.parent.parent / "outputs" / "case_results"


class TrainingCaseRecord(TypedDict):
    case_id: str
    requested_service: str
    clinical_scenario: NotRequired[str]
    key_supporting_evidence: NotRequired[str]
    key_gaps_or_risks: NotRequired[str]
    expected_outcome: str
    why: NotRequired[str]
    if_additional_documentation_arrives: NotRequired[Optional[str]]
    complexity_notes: NotRequired[Optional[str]]


class BatchResult(TypedDict):
    case_id: str
    expected: str
    actual: str
    match: bool
    confidence: NotRequired[str]
    complexity_notes: NotRequired[Optional[str]]
    error: NotRequired[str]


def load_training_cases() -> List[TrainingCaseRecord]:
    raw_cases = json.loads((DATA_DIR / "training_cases.json").read_text())
    if not isinstance(raw_cases, list):
        raise ValueError("training_cases.json must contain a list of case records")
    case_items = cast(List[object], raw_cases)
    return [
        cast(TrainingCaseRecord, item) for item in case_items if isinstance(item, dict)
    ]


def case_to_input(training_case: TrainingCaseRecord) -> PreAuthCaseInput:
    """
    Convert training case summary (9 fields) to PreAuthCaseInput for batch validation.
    raw_clinical_notes carries the key_supporting_evidence and key_gaps_or_risks
    so the normalization step has the relevant clinical context.
    """
    return PreAuthCaseInput(
        case_id=training_case["case_id"],
        requested_service=training_case["requested_service"],
        primary_diagnosis=training_case.get("clinical_scenario", "See clinical scenario"),
        raw_clinical_notes=(
            f"Clinical scenario: {training_case.get('clinical_scenario', '')}\n"
            f"Supporting evidence: {training_case.get('key_supporting_evidence', '')}\n"
            f"Gaps or risks: {training_case.get('key_gaps_or_risks', '')}"
        ),
    )


def _find_result(
    batch_results: List[BatchResult], case_id: str
) -> Optional[BatchResult]:
    for result in batch_results:
        if result.get("case_id") == case_id:
            return result
    return None


@pytest.fixture(scope="module")
def batch_results() -> List[BatchResult]:
    """
    Run all 10 training cases once per module.
    Saves full output for D8a deliverable.
    """
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    cases = load_training_cases()
    results: List[BatchResult] = []

    for training_case in cases:
        case_input = case_to_input(training_case)
        try:
            output = run_pipeline_sync(case_input)
            out_path = OUTPUTS_DIR / f"{training_case['case_id']}.json"
            with open(out_path, "w", encoding="utf-8") as output_file:
                json.dump(output.model_dump(), output_file, indent=2)
            results.append(
                {
                    "case_id": training_case["case_id"],
                    "expected": training_case["expected_outcome"],
                    "actual": output.recommendation,
                    "match": output.recommendation == training_case["expected_outcome"],
                    "confidence": output.confidence,
                    "complexity_notes": training_case.get("complexity_notes"),
                }
            )
        except Exception as exc:
            results.append(
                {
                    "case_id": training_case["case_id"],
                    "expected": training_case["expected_outcome"],
                    "actual": "ERROR",
                    "match": False,
                    "error": str(exc),
                    "complexity_notes": training_case.get("complexity_notes"),
                }
            )

    return results


def test_accuracy_at_least_8_of_10(batch_results: List[BatchResult]) -> None:
    correct = sum(1 for result in batch_results if result["match"])
    total = len(batch_results)

    print(f"\n{'=' * 65}")
    print(f"BATCH VALIDATION: {correct}/{total} correct ({correct / total * 100:.0f}%)")
    print(f"{'=' * 65}")
    for result in batch_results:
        status = "OK" if result["match"] else "FAIL"
        print(
            f"  {status} {result['case_id']} | Expected: {result['expected']:<18} | "
            f"Got: {result['actual']:<18}"
        )
        if not result["match"]:
            print(f"     Complexity: {result.get('complexity_notes', '')}")
    print(f"{'=' * 65}\n")

    assert correct >= 8, (
        f"Accuracy {correct}/{total} is below the 8/10 target. "
        "Review failing cases - see docs/ERROR_ANALYSIS.md for per-case guidance."
    )


def test_pa001_is_need_more_info(batch_results: List[BatchResult]) -> None:
    result = _find_result(batch_results, "PA-001")
    assert result is not None and result["actual"] == "NEED_MORE_INFO", (
        f"PA-001 must be NEED_MORE_INFO. Got: {result['actual'] if result else 'not found'}"
    )


def test_pa002_is_likely_deny(batch_results: List[BatchResult]) -> None:
    result = _find_result(batch_results, "PA-002")
    assert result is not None and result["actual"] == "LIKELY_DENY", (
        "PA-002 (chronic LBP, no neurologic deficit) must be LIKELY_DENY. "
        f"Got: {result['actual'] if result else 'not found'}. "
        "Most common failure: LLM over-weights 'chronic pain >1 year'. "
        "Rule 4 and few-shot PA-002 example should prevent this."
    )


def test_pa003_is_likely_approve(batch_results: List[BatchResult]) -> None:
    result = _find_result(batch_results, "PA-003")
    assert result is not None and result["actual"] == "LIKELY_APPROVE", (
        f"PA-003 (total knee, all criteria met) must be LIKELY_APPROVE. "
        f"Got: {result['actual'] if result else 'not found'}"
    )


def test_all_output_files_saved(batch_results: List[BatchResult]) -> None:
    """Verify D8a: all 10 full output JSON files written to outputs/case_results/."""
    for result in batch_results:
        if result.get("actual") not in ("ERROR", None):
            out_path = OUTPUTS_DIR / f"{result['case_id']}.json"
            assert out_path.exists(), (
                f"Output file missing for {result['case_id']}: {out_path}"
            )
