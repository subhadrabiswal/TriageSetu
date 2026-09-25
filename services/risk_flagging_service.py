"""
services/risk_flagging_service.py
------------------------------------
Rule-based, explainable risk tagging. Deliberately simple: a judge
or a clinician should be able to read this file top to bottom and
know exactly why a case got tagged Red, Yellow, or Green - no black
box, per the PRD's safety-first and explainability requirements.
"""

from app.models.triage_note import RiskCategory
from app.utils.constants import RED_FLAG_KEYWORDS, YELLOW_FLAG_KEYWORDS


def assess(raw_text: str, detected_symptoms: list[str]) -> dict:
    text_lower = raw_text.lower()

    red_hits = [kw for kw in RED_FLAG_KEYWORDS if kw in text_lower]
    if red_hits:
        return {
            "risk_category": RiskCategory.RED,
            "risk_score": 0.9,
            "risk_rationale_text": (
                "Marked urgent because the patient's own words include: "
                + ", ".join(red_hits)
                + ". Review immediately."
            ),
        }

    yellow_hits = [kw for kw in YELLOW_FLAG_KEYWORDS if kw in text_lower]
    if yellow_hits:
        return {
            "risk_category": RiskCategory.YELLOW,
            "risk_score": 0.6,
            "risk_rationale_text": (
                "Marked priority because the patient's own words include: "
                + ", ".join(yellow_hits)
                + ". Review before routine cases."
            ),
        }

    if detected_symptoms:
        rationale = (
            "No red or yellow-flag terms detected. Reported symptoms ("
            + ", ".join(detected_symptoms)
            + ") appear routine based on wording alone - reviewer judgment still applies."
        )
    else:
        rationale = (
            "No red or yellow-flag terms detected in the reported symptoms. "
            "Routine review recommended - reviewer judgment still applies."
        )

    return {
        "risk_category": RiskCategory.GREEN,
        "risk_score": 0.2,
        "risk_rationale_text": rationale,
    }
