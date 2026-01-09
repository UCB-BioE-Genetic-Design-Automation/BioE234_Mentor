import json
import re

STEP_ID = "040"
KEY = "ABSTRACT_SIGNATURE"
TITLE = "Identify the function signature"
NEXT_STEP = "050"
HASH_MODE = "json"
SUBMIT_STUB = (
    "sig_yaml = r'''\n"
    "<insert YAML here>\n"
    "'''\n"
    "mentor.submit_display(\"ABSTRACT_SIGNATURE\", sig_yaml)"
)


def render(state) -> str:
    code = (state.get("rbschooser2_code") or "").strip()
    if not code:
        return (
            "I do not have your generated code on record, so I cannot continue.\n\n"
            "Go back and submit your draft function code first. Then run `mentor.display()` to return here."
        )

    gemini_prompt = (
        "What is the signature of the function we just wrote?\n"
        "Explain it briefly, then express the signature as YAML"
    )

    return (
        "A function signature is the interface of a function: the function name, the inputs it accepts, and the output it returns.\n\n"
        "The important point: the signature is arbitrary. Gemini chose it. Different signatures imply different ways a user must call the function.\n\n"
        "In the same Gemini chat where you generated your function, ask Gemini to describe the signature in a formal way.\n\n"
        "Copy and paste this prompt into Gemini:\n\n"
        "```text\n"
        + gemini_prompt
        + "\n```\n\n"
        "Then paste the YAML Gemini returns here and submit it."
    )


def shape_check(answer):
    if not isinstance(answer, str):
        return False, "Expected YAML text (a string)."
    if not answer.strip():
        return False, "Submission was empty."
    return True, "ok"


def _strip_code_fences(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z0-9_+-]*\n", "", s)
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def validate(answer, state):
    code = (state.get("rbschooser2_code") or "").strip()
    if not code:
        return False, "Draft code is missing. Go back and submit the function code first.", {}

    s = _strip_code_fences(str(answer))
    if len(s.strip()) < 10:
        return False, "This looks too short. Paste the YAML Gemini returned.", {"chars": len(s.strip())}

    try:
        import yaml
        yaml.safe_load(s)
    except Exception:
        return False, "I could not parse this as YAML. Paste the YAML block Gemini returned.", {}

    state["abstract_signature_yaml"] = s
    return True, "Signature recorded.", {"chars": len(s)}
