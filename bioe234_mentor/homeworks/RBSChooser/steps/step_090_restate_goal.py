from __future__ import annotations

from typing import Any, Dict, Tuple


STEP_ID = "090"
KEY = "RESTATE_GOAL"
TITLE = "Restate the goal"
NEXT_STEP = "100"
HASH_MODE = "json"


def render(state: Dict[str, Any]) -> str:
    return (
        "Restate the RBSChooser2 goal in plain language.\n\n"
        "Include three things:\n"
        "1) What the input is\n"
        "2) What the output is\n"
        "3) One thing the output must not include\n\n"
        "Submit a short paragraph or 3 bullet points.\n\n"
        "Submission (copy and edit):\n"
        "```python\n"
        "mentor.submit_display('RESTATE_GOAL', 'INPUT: ...\\nOUTPUT: ...\\nMUST NOT: ...')\n"
        "```"
    )


def shape_check(answer: Any) -> Tuple[bool, str]:
    if not isinstance(answer, str) or not answer.strip():
        return False, "Submit non-empty text."

    text = answer.strip()

    # Lightweight structure expectations to keep the response aligned.
    has_input = "input" in text.lower()
    has_output = "output" in text.lower()

    if not (has_input and has_output):
        return False, "Include both an INPUT and an OUTPUT in your text."

    return True, ""


def validate(answer: Any, state: Dict[str, Any]):
    # No correctness grading here, just accept if shape_check passed.
    return True, "Thanks. We'll use this as a shared contract for the build steps.", {}
