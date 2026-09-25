"""
ai/prompts.py
---------------
Prompt templates for the LLM-assisted parts of triage note drafting.
Kept separate from llm_client.py so the wording can be reviewed and
tuned without touching any request/response handling code.
"""

SUMMARIZATION_SYSTEM_PROMPT = """You are a triage-support assistant for Indian government and \
institutional health facilities. You help a health worker capture a patient's case clearly. \
You are NOT a diagnostic tool: never suggest a diagnosis, medication, or treatment. \
You only organize what the patient reported into a structured note for a nurse or doctor to review.

Respond with ONLY a JSON object (no other text) with these exact keys:
{
  "summary": "2-4 sentence plain-language summary of the case",
  "timeline": [{"when": "string, e.g. '3 days ago'", "event": "string"}],
  "detected_symptoms": ["short symptom phrase", "..."],
  "missing_info": ["specific field missing, e.g. 'duration of fever'"],
  "follow_up_questions": ["one specific question per missing field"]
}
"""


def build_summarization_prompt(raw_text: str, ocr_text: str | None, language: str) -> str:
    parts = [f"Patient-reported symptoms (language: {language}):\n{raw_text.strip()}"]
    if ocr_text and ocr_text.strip():
        parts.append(f"\nText extracted from an uploaded report/photo:\n{ocr_text.strip()}")
    parts.append(
        "\nProduce the structured JSON described in your instructions. "
        "If information is missing (duration, severity, prior conditions, medications), "
        "list it in missing_info and write a specific follow-up question for each."
    )
    return "\n".join(parts)
