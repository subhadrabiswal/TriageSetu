"""
ai/evidence_mapper.py
------------------------
Maps each detected symptom back to the sentence in the patient's own
words that mentioned it. This is what lets a reviewer see *why* the
system said what it said, instead of trusting a summary blindly -
directly supporting the human-review and explainability requirements.
"""

import re


def map_evidence(raw_text: str, detected_symptoms: list[str]) -> list[dict]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", raw_text) if s.strip()]
    if not sentences:
        sentences = [raw_text.strip()] if raw_text.strip() else []

    evidence = []
    for symptom in detected_symptoms:
        matching_sentence = next(
            (s for s in sentences if symptom in s.lower()),
            None,
        )
        evidence.append({
            "symptom": symptom,
            "source_snippet": matching_sentence or raw_text[:140],
        })
    return evidence
