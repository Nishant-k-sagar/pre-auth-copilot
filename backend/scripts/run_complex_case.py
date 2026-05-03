"""
Runs the full pipeline on PA-001 (complex case, full 19-row packet).
Produces outputs/complex_case_output.json (D4 deliverable).

Usage:
    cd backend
    python scripts/run_complex_case.py
"""

import asyncio
import json
import sys
from typing import Dict, List, Optional, TypedDict, cast
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from skill.schema import PreAuthCaseInput, SourcedField
from skill.pipeline import run_pipeline


class CaseRow(TypedDict):
    section: str
    field: str
    value: Optional[str]
    source: Optional[str]
    notes: Optional[str]


def build_complex_case_input() -> PreAuthCaseInput:
    """
    Build PA-001 PreAuthCaseInput from the full 19-row clinical packet.
    Uses SourcedField for the 3 attribution-critical fields.
    Uses the parsed complex_case.json — not the training case summary row.
    """
    data_path = Path(__file__).parent.parent / "data" / "complex_case.json"
    rows = cast(List[CaseRow], json.loads(data_path.read_text()))

    field_map: Dict[str, CaseRow] = {
        r["field"].lower().strip(): r
        for r in rows
    }

    def get_value(name: str) -> Optional[str]:
        row = field_map.get(name.lower())
        return row.get("value") if row else None

    def get_row(name: str) -> Optional[CaseRow]:
        return field_map.get(name.lower())

    def get_sourced(name: str) -> Optional[SourcedField]:
        row = field_map.get(name.lower())
        if not row or not row.get("value"):
            return None
        return SourcedField(
            value=row.get("value"),
            source=row.get("source"),
            source_date=None,
        )

    secondary_raw = get_value("secondary diagnoses") or get_value("comorbidities")
    secondary_diagnoses = None
    if secondary_raw:
        secondary_diagnoses = [
            s.strip() for s in str(secondary_raw).replace(";", ",").split(",") if s.strip()
        ]

    conservative_care = get_value("conservative care")
    prior_conservative_treatment = [conservative_care] if conservative_care else None

    requested_service_row: CaseRow = get_row("requested service") or {
        "section": "",
        "field": "",
        "value": None,
        "source": None,
        "notes": None,
    }
    requested_service_notes = str(requested_service_row.get("notes") or "")
    site_of_care = get_value("site of care") or get_value("site_of_care")
    if not site_of_care and "inpatient" in requested_service_notes.lower():
        site_of_care = "Inpatient"

    requested_los = get_value("expected los")
    if not requested_los and "2 midnights" in requested_service_notes.lower():
        requested_los = "2 midnights"

    age_raw = get_value("age / sex") or get_value("age")
    age = None
    sex = None
    if age_raw:
        parts = [p.strip() for p in str(age_raw).split("/")]
        if parts and parts[0]:
            try:
                age = int(parts[0])
            except (ValueError, IndexError):
                pass
        if len(parts) > 1 and parts[1]:
            sex = parts[1]

    return PreAuthCaseInput(
        case_id="PA-001",
        requested_service=get_value("requested service") or "Unknown",
        site_of_care=site_of_care,
        requested_los=requested_los,
        payer_policy_version=get_value("payer policy used") or get_value("payer policy"),
        payer_policy_excerpt=get_value("payer policy excerpt"),
        age=age,
        sex=sex,
        primary_diagnosis=get_value("primary diagnosis") or "Unknown",
        secondary_diagnoses=secondary_diagnoses
        or [
            s.strip()
            for s in str(get_value("medical risk factors") or "").replace(";", ",").split(",")
            if s.strip()
        ]
        or None,
        symptom_duration=get_value("symptom duration"),
        pain_severity=get_value("pain severity"),
        functional_impairment_adls=get_sourced("adl impact"),
        objective_neurologic_deficits=get_sourced("objective findings"),
        imaging_findings=get_sourced("mri cervical spine") or get_sourced("imaging"),
        prior_conservative_treatment=prior_conservative_treatment,
        response_to_prior_treatment=get_value("response"),
        current_medications=[
            s.strip() for s in str(get_value("current medications") or "").replace(";", ",").split(",") if s.strip()
        ] or None,
        complications_red_flags=get_value("recent events"),
        contradictory_flags=get_value("contradiction"),
        missing_records=get_value("missing documentation"),
        ordering_provider_specialty=get_value("ordering provider specialty"),
    )


async def main():
    print("Building PA-001 complex case input (full 19-row packet)...")
    case_input = build_complex_case_input()

    print("Running pipeline...")
    output = await run_pipeline(case_input)

    out_dir = Path(__file__).parent.parent.parent / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "complex_case_output.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output.model_dump(), f, indent=2)

    print(f"\nOutput saved: {out_path}")
    print(f"\nRecommendation:    {output.recommendation}")
    print(f"Confidence:        {output.confidence}")
    print(f"Criteria MET:      {output.criteria_met}")
    print(f"Criteria PARTIAL:  {output.criteria_partial_or_unmet}")
    print(f"appeal_direction:  {output.appeal_direction}")
    print(f"flip_condition:    {output.flip_condition[:60] if output.flip_condition else None}...")
    print(f"Pipeline time:     {output.processing_time_ms}ms")
    print(f"Missing info ({len(output.missing_information)} items):")
    for item in output.missing_information:
        print(f"  - {item}")

    # Gold standard assertions
    assert output.recommendation == "NEED_MORE_INFO", \
        f"Expected NEED_MORE_INFO, got {output.recommendation}"
    assert set(output.criteria_met) == {"C1", "C2", "C3"}, \
        f"Expected C1/C2/C3 MET, got {output.criteria_met}"
    assert set(output.criteria_partial_or_unmet) == {"C4", "C5", "C6"}, \
        f"Expected C4/C5/C6 PARTIAL, got {output.criteria_partial_or_unmet}"
    assert output.appeal_direction is None, \
        f"appeal_direction must be null for NEED_MORE_INFO, got: {output.appeal_direction}"
    assert output.flip_condition, \
        "flip_condition must be populated for NEED_MORE_INFO"

    print("\nGold standard assertions passed.")


if __name__ == "__main__":
    asyncio.run(main())
