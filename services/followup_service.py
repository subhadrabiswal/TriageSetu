"""
services/followup_service.py
--------------------------------
Cleans up the follow-up question list: removes duplicates while
keeping the original order, and caps the list so a reviewer isn't
handed an overwhelming checklist.
"""

MAX_QUESTIONS = 4


def dedupe_questions(questions: list[str]) -> list[str]:
    seen = set()
    result = []
    for q in questions:
        q_clean = q.strip()
        if q_clean and q_clean.lower() not in seen:
            seen.add(q_clean.lower())
            result.append(q_clean)
    return result[:MAX_QUESTIONS]
