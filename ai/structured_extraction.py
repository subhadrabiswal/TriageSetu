"""
ai/structured_extraction.py
------------------------------
Turns raw patient text (+ any OCR'd report text) into the structured
shape a triage note needs. Tries the LLM first; if it's not
configured or the call/parse fails, falls back to a transparent
rule-based extraction so the flow never breaks.
"""

import json
import re

from app.ai import llm_client
from app.ai.prompts import SUMMARIZATION_SYSTEM_PROMPT, build_summarization_prompt
from app.utils.constants import (
    RED_FLAG_KEYWORDS, YELLOW_FLAG_KEYWORDS, GENERAL_SYMPTOM_KEYWORDS,
    DURATION_HINTS, SEVERITY_HINTS,
)


def extract(raw_text: str, ocr_text: str | None, language: str) -> dict:
    llm_result = _try_llm(raw_text, ocr_text, language)
    if llm_result is not None:
        llm_result["source"] = "llm"
        return llm_result

    result = _rule_based(raw_text, ocr_text)
    result["source"] = "rule_based"
    return result


def _try_llm(raw_text: str, ocr_text: str | None, language: str) -> dict | None:
    if not llm_client.is_configured():
        return None

    prompt = build_summarization_prompt(raw_text, ocr_text, language)
    raw_response = llm_client.call(SUMMARIZATION_SYSTEM_PROMPT, prompt)
    if raw_response is None:
        return None

    try:
        # The model is instructed to return only JSON, but strip any
        # accidental code-fence wrapping just in case.
        cleaned = raw_response.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        parsed = json.loads(cleaned)
        return {
            "summary": parsed.get("summary", ""),
            "timeline": parsed.get("timeline", []),
            "detected_symptoms": parsed.get("detected_symptoms", []),
            "missing_info": parsed.get("missing_info", []),
            "follow_up_questions": parsed.get("follow_up_questions", []),
        }
    except (json.JSONDecodeError, AttributeError):
        return None


def _rule_based(raw_text: str, ocr_text: str | None) -> dict:
    text_lower = raw_text.lower()

    detected_symptoms = sorted({
        kw for kw in (RED_FLAG_KEYWORDS + YELLOW_FLAG_KEYWORDS + GENERAL_SYMPTOM_KEYWORDS)
        if kw in text_lower
    })

    missing_info = []
    follow_up_questions = []

    rules = [
        { "keywords": ['din','day','since'], "ifMissing": "Since how many days?", "missingInfo": "duration of symptoms" },
        { "keywords": ['allerg'], "ifMissing": "Any known allergies or medications?", "missingInfo": "allergies or medications" },
        { "keywords": ['bukhar','fever'], "ifPresent": True, "unless": ['mild','high','tez'], 
          "question": "Is the fever mild or high?", "missingInfo": "fever severity" },
        { "keywords": ['dard','pain'], "ifPresent": True, "unless": ['mild','severe','halka'], 
          "question": "How severe is the pain?", "missingInfo": "pain severity" }
    ]

    for rule in rules:
        kw_match = any(kw in text_lower for kw in rule["keywords"])
        if "ifMissing" in rule:
            if not kw_match:
                follow_up_questions.append(rule["ifMissing"])
                if "missingInfo" in rule:
                    missing_info.append(rule["missingInfo"])
        elif rule.get("ifPresent"):
            if kw_match:
                unless_match = any(un in text_lower for un in rule.get("unless", []))
                if not unless_match and "question" in rule:
                    follow_up_questions.append(rule["question"])
                    if "missingInfo" in rule:
                        missing_info.append(rule["missingInfo"])

    follow_up_questions = follow_up_questions[:4]

    summary_source = raw_text.strip()
    summary = summary_source if len(summary_source) <= 220 else summary_source[:217] + "..."
    if ocr_text and ocr_text.strip():
        summary += " An uploaded report/photo was also attached for this case."

    timeline = [{"when": "at intake", "event": summary_source[:140]}]

    return {
        "summary": summary,
        "timeline": timeline,
        "detected_symptoms": detected_symptoms,
        "missing_info": missing_info,
        "follow_up_questions": follow_up_questions,
    }
