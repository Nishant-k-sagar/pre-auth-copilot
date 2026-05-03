"""
Deep assertions for PA-001 complex case.

Each assertion maps to a specific evaluator intent from the workbook's
Notes column (Complex_Case_Input) and Expected_Skill_Behavior column
(Complex_Case_Outcome).

scope="module" on the output fixture: runs the pipeline ONCE for the whole
module to avoid repeated API calls.

Run:
    Set-Location backend; pytest tests/test_complex_case.py -v
"""

import json
import sys
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from conftest import run_pipeline_sync
from scripts.run_complex_case import build_complex_case_input
from skill.schema import CriterionResult, PreAuthSkillOutput


@pytest.fixture(scope="module")
def output() -> PreAuthSkillOutput:
    """Run pipeline once for the whole module."""
    return run_pipeline_sync(build_complex_case_input())


def _find_criterion(
    output: PreAuthSkillOutput, criterion_id: str
) -> Optional[CriterionResult]:
    for criterion in output.criteria_results:
        if criterion.criterion_id == criterion_id:
            return criterion
    return None


def _require_criterion(
    output: PreAuthSkillOutput, criterion_id: str
) -> CriterionResult:
    criterion = _find_criterion(output, criterion_id)
    assert criterion is not None, f"{criterion_id} criterion result missing from output"
    return criterion


def test_recommendation_is_need_more_info(output: PreAuthSkillOutput) -> None:
    assert output.recommendation == "NEED_MORE_INFO", (
        f"Expected NEED_MORE_INFO, got {output.recommendation}. "
        "Clinical necessity is established (C1/C2/C3 MET) but packet is incomplete "
        "(C4/C5/C6 PARTIAL). This must be NEED_MORE_INFO, not LIKELY_DENY."
    )


def test_confidence_is_medium_or_low(output: PreAuthSkillOutput) -> None:
    assert output.confidence in ("MEDIUM", "LOW"), (
        f"Core criteria MET but secondary all PARTIAL -> MEDIUM or LOW confidence. "
        f"Got: {output.confidence}"
    )


def test_criteria_met_set(output: PreAuthSkillOutput) -> None:
    assert set(output.criteria_met) == {"C1", "C2", "C3"}, (
        f"Expected C1, C2, C3 MET. Got: {output.criteria_met}. "
        "The gold standard requires the documentation/site-of-care criteria to remain PARTIAL."
    )


def test_criteria_partial_set(output: PreAuthSkillOutput) -> None:
    assert set(output.criteria_partial_or_unmet) == {"C4", "C5", "C6"}, (
        f"Expected C4, C5, C6 PARTIAL. Got: {output.criteria_partial_or_unmet}. "
        "PA-001 is clinically supportable but not payer-ready."
    )


def test_c4_is_partial(output: PreAuthSkillOutput) -> None:
    c4 = _require_criterion(output, "C4")
    assert c4.status == "PARTIAL", (
        f"C4 must be PARTIAL (ADL in PT note only, not in surgeon consult). Got: {c4.status}"
    )


def test_c4_evidence_cites_pt_note(output: PreAuthSkillOutput) -> None:
    c4 = _require_criterion(output, "C4")
    evidence = (c4.supporting_evidence or "").lower()
    assert "pt" in evidence or "physical therapy" in evidence, (
        f"C4 supporting_evidence must reference PT note as source. Got: {c4.supporting_evidence}"
    )


def test_c4_gap_mentions_surgeon(output: PreAuthSkillOutput) -> None:
    c4 = _require_criterion(output, "C4")
    gap = (c4.gap_or_risk or "").lower()
    assert "surgeon" in gap or "surgical" in gap or "consult" in gap, (
        f"C4 gap_or_risk must flag that latest surgeon consult lacks ADL statement. "
        f"Got: {c4.gap_or_risk}"
    )


def test_c2_is_met(output: PreAuthSkillOutput) -> None:
    c2 = _require_criterion(output, "C2")
    assert c2.status == "MET", (
        "C2 must be MET - specialist exam confirms deficit. "
        f"PCP note conflict does not override recent specialist. Got: {c2.status}"
    )


def test_c2_contradiction_acknowledged(output: PreAuthSkillOutput) -> None:
    c2 = _require_criterion(output, "C2")
    all_c2_text = ((c2.supporting_evidence or "") + " " + (c2.gap_or_risk or "")).lower()
    assert any(
        word in all_c2_text
        for word in ["pcp", "conflict", "contradict", "intact", "earlier", "older"]
    ), (
        "C2 must acknowledge the PCP note contradiction ('strength grossly intact'). "
        f"Got evidence: {c2.supporting_evidence} | gap: {c2.gap_or_risk}"
    )


def test_near_fall_appears_in_output(output: PreAuthSkillOutput) -> None:
    all_text = json.dumps(output.model_dump()).lower()
    assert "fall" in all_text, (
        "Near-fall history (documented in PT note, absent from request form) "
        "must appear somewhere in the output. It is a key safety signal for inpatient justification."
    )


def test_provider_query_mentions_adl(output: PreAuthSkillOutput) -> None:
    provider_query = output.provider_query.lower()
    assert any(
        word in provider_query
        for word in ["adl", "daily living", "functional", "buttoning", "dropping", "stairs"]
    ), f"Provider query must ask for ADL documentation. Got: {output.provider_query[:200]}"


def test_provider_query_mentions_inpatient_justification(
    output: PreAuthSkillOutput,
) -> None:
    provider_query = output.provider_query.lower()
    assert any(
        word in provider_query
        for word in ["inpatient", "site", "monitoring", "admission", "outpatient", "asc"]
    ), (
        "Provider query must ask for inpatient site-of-care justification. "
        f"Got: {output.provider_query[:200]}"
    )


def test_provider_query_mentions_comorbidities(output: PreAuthSkillOutput) -> None:
    provider_query = output.provider_query.lower()
    assert any(
        word in provider_query
        for word in [
            "osa",
            "sleep apnea",
            "obesity",
            "diabetes",
            "bmi",
            "fall",
            "comorbidit",
            "risk",
            "justification",
        ]
    ), (
        "Provider query must reference comorbidities/risks justifying inpatient "
        f"(OSA, obesity, diabetes, fall risk, etc). Got: {output.provider_query[:200]}"
    )


def test_appeal_direction_is_null(output: PreAuthSkillOutput) -> None:
    assert output.appeal_direction is None, (
        "appeal_direction must be null for NEED_MORE_INFO - case has not been denied. "
        f"Got: {output.appeal_direction}"
    )


def test_flip_condition_is_populated(output: PreAuthSkillOutput) -> None:
    assert output.flip_condition is not None, (
        "flip_condition must be populated for NEED_MORE_INFO - it answers "
        "'additional documentation that could improve the outcome'."
    )
    assert len(output.flip_condition) > 20, (
        f"flip_condition too short to be meaningful: '{output.flip_condition}'"
    )


def test_pain_score_not_sole_approval_evidence(output: PreAuthSkillOutput) -> None:
    evidence_text = " ".join(
        snippet.excerpt for snippet in output.supporting_evidence
    ).lower()
    if "8/10" in evidence_text:
        assert any(
            word in evidence_text
            for word in ["not sufficient", "alone", "objective", "insufficient"]
        ), (
            "Pain severity '8/10' appears in supporting_evidence without qualification. "
            "Pain alone is never sufficient - this must be explicitly noted."
        )


def test_criteria_results_count(output: PreAuthSkillOutput) -> None:
    assert len(output.criteria_results) >= 6, (
        f"Expected >=6 criteria results (C1-C6). Got: {len(output.criteria_results)}"
    )


def test_supporting_evidence_has_sources(output: PreAuthSkillOutput) -> None:
    for snippet in output.supporting_evidence:
        assert snippet.source, f"EvidenceSnippet missing source: {snippet}"
        assert snippet.excerpt, f"EvidenceSnippet missing excerpt: {snippet}"


def test_missing_information_has_minimum_items(output: PreAuthSkillOutput) -> None:
    assert isinstance(output.missing_information, list)
    assert len(output.missing_information) >= 2, (
        "At minimum: surgeon ADL statement gap and inpatient justification gap "
        f"should be listed. Got: {output.missing_information}"
    )
