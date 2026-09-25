"""
services/summarization_service.py
------------------------------------
Pure orchestration of the AI layer: takes raw text in, returns a
structured dict out. Does not touch the database - triage_service.py
is responsible for persisting the result. Keeping this side-effect
free makes it easy to unit test.
"""

from app.ai.structured_extraction import extract
from app.ai.evidence_mapper import map_evidence
from app.services.risk_flagging_service import assess
from app.services.timeline_service import normalize_timeline
from app.services.followup_service import dedupe_questions


def build_triage_draft(raw_text: str, ocr_text: str | None, language: str) -> dict:
    extraction = extract(raw_text, ocr_text, language)

    risk = assess(raw_text, extraction.get("detected_symptoms", []))
    evidence = map_evidence(raw_text, extraction.get("detected_symptoms", []))

    return {
        "summary_text": extraction.get("summary", ""),
        "timeline_json": normalize_timeline(extraction.get("timeline", [])),
        "missing_info_json": extraction.get("missing_info", []),
        "follow_up_questions_json": dedupe_questions(extraction.get("follow_up_questions", [])),
        "risk_category": risk["risk_category"],
        "risk_score": risk["risk_score"],
        "risk_rationale_text": risk["risk_rationale_text"],
        "evidence": evidence,
        "extraction_source": extraction.get("source", "rule_based"),
    }
