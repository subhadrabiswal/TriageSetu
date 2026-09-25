"""
services/timeline_service.py
--------------------------------
Normalizes whatever timeline data the extraction step produced (LLM
or rule-based) into a consistent shape before it's stored.
"""


def normalize_timeline(raw_timeline) -> list[dict]:
    if not raw_timeline or not isinstance(raw_timeline, list):
        return []

    normalized = []
    for entry in raw_timeline:
        if isinstance(entry, dict):
            normalized.append({
                "when": str(entry.get("when", "unspecified")),
                "event": str(entry.get("event", "")),
            })
    return normalized
