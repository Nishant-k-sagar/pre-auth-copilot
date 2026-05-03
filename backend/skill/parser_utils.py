"""
Shared workbook parsing functions.

Lives in skill/ so it is importable as skill.parser_utils by:
  - scripts/parse_workbook.py  (CLI)
  - main.py upload route       (top-level import, fails fast at startup if missing)

Field count note:
  The Patient_Data_Aspects sheet has exactly 30 rows (IDs 1-30).
  Field 19 is "Medication contraindications / intolerance" whose description
  already covers allergies, side effects, and intolerances.
  The Problem Statement lists "allergies" as an input packet document type,
  not as a separate schema field. Drug/substance allergies are extracted into
  field 19 by the normalization prompt - no separate field is added.
"""

import math
from typing import Dict, List, Optional, Sequence

from typing_extensions import TypedDict

from openpyxl import Workbook


VALID_LABELS = {"LIKELY_APPROVE", "NEED_MORE_INFO", "LIKELY_DENY"}


def clean_value(value: object) -> Optional[str]:
    """Normalize NaN, None, and empty strings to None; stringify everything else."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value).strip() or None


def _read_sheet_rows(workbook: Workbook, sheet_name: str) -> List[List[object]]:
    """Read an entire sheet as raw rows to support mixed-layout workbook tabs."""
    worksheet = workbook[sheet_name]
    rows: List[List[object]] = []
    for raw_row in worksheet.iter_rows(values_only=True):
        rows.append([cell if cell is not None else "" for cell in raw_row])
    return rows


def _normalize_header(value: object) -> str:
    return str(value).strip().lower().replace("_", " ")


def _find_header_index(rows: List[List[object]], expected_columns: Sequence[str]) -> int:
    """Find the row containing all expected header labels."""
    expected = {_normalize_header(column) for column in expected_columns}
    for row_index, row in enumerate(rows):
        values = {_normalize_header(value) for value in row if str(value).strip()}
        if expected.issubset(values):
            return row_index
    raise ValueError(
        f"Could not find header row containing columns: {', '.join(expected_columns)}"
    )


def _build_column_index(
    header_row: Sequence[object],
    expected_columns: Sequence[str],
) -> Dict[str, int]:
    """Map canonical expected column names to indices in the actual header row."""
    normalized_header = [_normalize_header(value) for value in header_row]
    index_map: Dict[str, int] = {}
    for expected in expected_columns:
        normalized_expected = _normalize_header(expected)
        try:
            index_map[expected] = normalized_header.index(normalized_expected)
        except ValueError as exc:
            raise ValueError(f"Required workbook column missing: {expected}") from exc
    return index_map


def _get_row_value(row: Sequence[object], index: int) -> Optional[str]:
    if index >= len(row):
        return None
    return clean_value(row[index])


class TrainingCaseRow(TypedDict, total=False):
    """Type for a training case row from Training_Cases sheet."""

    case_id: Optional[str]
    requested_service: Optional[str]
    clinical_scenario: Optional[str]
    key_supporting_evidence: Optional[str]
    key_gaps_or_risks: Optional[str]
    expected_outcome: Optional[str]
    why: Optional[str]
    if_additional_documentation_arrives: Optional[str]
    complexity_notes: Optional[str]


class ComplexCaseRow(TypedDict, total=False):
    """Type for a complex case row from Complex_Case_Input sheet."""

    section: Optional[str]
    field: Optional[str]
    value: Optional[str]
    source: Optional[str]
    notes: Optional[str]


class SchemaFieldRow(TypedDict, total=False):
    """Type for a schema field row from Patient_Data_Aspects sheet."""

    id: Optional[int]
    category: Optional[str]
    aspect: Optional[str]
    description: Optional[str]
    typical_type: Optional[str]
    example_value: Optional[str]
    why_it_matters: Optional[str]


class ExpectedOutcomeCriterionRow(TypedDict):
    """Type for one criterion row in the expected outcome sheet."""

    criterion_id: Optional[str]
    policy_criterion: Optional[str]
    status: Optional[str]
    supporting_evidence: Optional[str]
    gap_risk: Optional[str]
    expected_skill_behavior: Optional[str]


class ExpectedOutcome(TypedDict, total=False):
    """Type for expected outcome from Complex_Case_Outcome sheet."""

    expected_recommendation: Optional[str]
    rationale: Optional[str]
    provider_query: Optional[str]
    flip_condition: Optional[str]
    criteria: List[ExpectedOutcomeCriterionRow]


def parse_training_cases(workbook: Workbook) -> List[TrainingCaseRow]:
    """Parse the `Training_Cases` sheet into the 10 summary records."""
    expected_columns = [
        "Case_ID",
        "Requested_Service",
        "Clinical_Scenario",
        "Key_Supporting_Evidence",
        "Key_Gaps_or_Risks",
        "Expected_Outcome",
        "Why",
        "If Additional Documentation Arrives",
        "Complexity_Notes",
    ]
    rows = _read_sheet_rows(workbook, "Training_Cases")
    header_index = _find_header_index(rows, expected_columns)
    column_index = _build_column_index(rows[header_index], expected_columns)

    records: List[TrainingCaseRow] = []
    for row in rows[header_index + 1 :]:
        case_id = _get_row_value(row, column_index["Case_ID"])
        if not case_id or case_id.lower() == "case id":
            continue
        records.append(
            {
                "case_id": case_id,
                "requested_service": _get_row_value(
                    row, column_index["Requested_Service"]
                ),
                "clinical_scenario": _get_row_value(
                    row, column_index["Clinical_Scenario"]
                ),
                "key_supporting_evidence": _get_row_value(
                    row, column_index["Key_Supporting_Evidence"]
                ),
                "key_gaps_or_risks": _get_row_value(
                    row, column_index["Key_Gaps_or_Risks"]
                ),
                "expected_outcome": _get_row_value(
                    row, column_index["Expected_Outcome"]
                ),
                "why": _get_row_value(row, column_index["Why"]),
                "if_additional_documentation_arrives": _get_row_value(
                    row, column_index["If Additional Documentation Arrives"]
                ),
                "complexity_notes": _get_row_value(
                    row, column_index["Complexity_Notes"]
                ),
            }
        )
    return records


def parse_patient_data_schema(workbook: Workbook) -> List[SchemaFieldRow]:
    """Parse the exact 30 patient-data schema rows from the workbook."""
    expected_columns = [
        "#",
        "Category",
        "Aspect",
        "Description",
        "Typical_Type",
        "Example_Value",
        "Why_It_Matters",
    ]
    rows = _read_sheet_rows(workbook, "Patient_Data_Aspects")
    header_index = _find_header_index(rows, expected_columns)
    column_index = _build_column_index(rows[header_index], expected_columns)

    records: List[SchemaFieldRow] = []
    for row in rows[header_index + 1 :]:
        raw_id = _get_row_value(row, column_index["#"])
        if raw_id is None:
            continue
        try:
            parsed_id = int(raw_id)
        except ValueError:
            continue
        records.append(
            {
                "id": parsed_id,
                "category": _get_row_value(row, column_index["Category"]),
                "aspect": _get_row_value(row, column_index["Aspect"]),
                "description": _get_row_value(row, column_index["Description"]),
                "typical_type": _get_row_value(row, column_index["Typical_Type"]),
                "example_value": _get_row_value(row, column_index["Example_Value"]),
                "why_it_matters": _get_row_value(
                    row, column_index["Why_It_Matters"]
                ),
            }
        )
    return records


def parse_complex_case(workbook: Workbook) -> List[ComplexCaseRow]:
    """Parse all rows from `Complex_Case_Input`, preserving source and notes."""
    expected_columns = ["Section", "Field", "Value", "Source", "Notes"]
    rows = _read_sheet_rows(workbook, "Complex_Case_Input")
    header_index = _find_header_index(rows, expected_columns)
    column_index = _build_column_index(rows[header_index], expected_columns)

    records: List[ComplexCaseRow] = []
    for row in rows[header_index + 1 :]:
        record: ComplexCaseRow = {
            "section": _get_row_value(row, column_index["Section"]),
            "field": _get_row_value(row, column_index["Field"]),
            "value": _get_row_value(row, column_index["Value"]),
            "source": _get_row_value(row, column_index["Source"]),
            "notes": _get_row_value(row, column_index["Notes"]),
        }
        if record["section"] is not None or record["field"] is not None:
            records.append(record)
    return records


def parse_expected_outcome(workbook: Workbook) -> ExpectedOutcome:
    """
    Parse `Complex_Case_Outcome`.

    The sheet is mixed-layout:
      - top rows: summary key/value pairs
      - middle rows: criteria table
      - later rows: provider query and flip condition
    """
    rows = _read_sheet_rows(workbook, "Complex_Case_Outcome")
    outcome: ExpectedOutcome = {
        "expected_recommendation": None,
        "rationale": None,
        "provider_query": None,
        "flip_condition": None,
        "criteria": [],
    }

    for row in rows:
        row_values = [clean_value(value) for value in row]
        if all(value is None for value in row_values):
            continue

        cell0 = row_values[0] or ""
        cell1 = row_values[1] if len(row_values) > 1 else None
        lower0 = cell0.lower()

        if len(cell0) == 2 and cell0.startswith("C") and cell0[1].isdigit():
            outcome["criteria"].append(
                {
                    "criterion_id": cell0,
                    "policy_criterion": cell1,
                    "status": row_values[2] if len(row_values) > 2 else None,
                    "supporting_evidence": (
                        row_values[3] if len(row_values) > 3 else None
                    ),
                    "gap_risk": row_values[4] if len(row_values) > 4 else None,
                    "expected_skill_behavior": (
                        row_values[5] if len(row_values) > 5 else None
                    ),
                }
            )
            continue

        if "recommendation" in lower0 and "expected" in lower0:
            outcome["expected_recommendation"] = cell1
        elif "rationale" in lower0:
            outcome["rationale"] = cell1
        elif "provider query" in lower0 or "provider_query" in lower0:
            outcome["provider_query"] = cell1
        elif "flip" in lower0 or ("would" in lower0 and "approve" in lower0):
            outcome["flip_condition"] = cell1

    return outcome


def validate_parsed_data(
    training_cases: List[TrainingCaseRow],
    schema_fields: List[SchemaFieldRow],
    complex_case: List[ComplexCaseRow],
    expected_outcome: ExpectedOutcome,
) -> bool:
    """Print validation summary and return True if all checks pass."""
    errors: List[str] = []

    if len(training_cases) != 10:
        errors.append(f"Training cases: expected 10, got {len(training_cases)}")
    for training_case in training_cases:
        if not training_case.get("case_id"):
            errors.append(f"Training case missing case_id: {training_case}")
        if training_case.get("expected_outcome") not in VALID_LABELS:
            errors.append(
                f"Invalid label '{training_case.get('expected_outcome')}' "
                f"for {training_case.get('case_id')}"
            )

    if len(schema_fields) != 30:
        errors.append(f"Schema fields: expected 30, got {len(schema_fields)}")

    if len(complex_case) < 15:
        errors.append(f"Complex case rows: expected ~19, got {len(complex_case)}")

    if not expected_outcome.get("expected_recommendation"):
        errors.append("expected_outcome missing expected_recommendation")
    if len(expected_outcome.get("criteria", [])) < 4:
        errors.append(
            "Expected outcome criteria: expected >=4, "
            f"got {len(expected_outcome.get('criteria', []))}"
        )
    if not expected_outcome.get("flip_condition"):
        errors.append("flip_condition missing from expected_outcome")

    print("\n=== PARSE WORKBOOK VALIDATION ===")
    print(f"  Training cases:       {len(training_cases)}/10")
    print(f"  Schema fields:        {len(schema_fields)}/30")
    print(f"  Complex case rows:    {len(complex_case)}")
    print(f"  Criteria (gold):      {len(expected_outcome.get('criteria', []))}")
    print(f"  Expected label:       {expected_outcome.get('expected_recommendation')}")
    flip_status = "present" if expected_outcome.get("flip_condition") else "MISSING"
    print(f"  Flip condition:       {flip_status}")

    if errors:
        print("\nERRORS:")
        for error in errors:
            print(f"   {error}")
        return False

    print("\nAll checks passed.")
    return True
