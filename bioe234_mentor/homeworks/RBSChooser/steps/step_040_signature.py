import json
import re

STEP_ID = "040"
KEY = "RBSCHOOSER2_SIGNATURE"
TITLE = "Identify the function signature"
NEXT_STEP = "050"
HASH_MODE = "json"
SUBMIT_STUB = (
    "sig_yaml = r'''name: RBSChooser2\n"
    "inputs:\n"
    "  - name: dna\n"
    "    type: string\n"
    "    description: ...\n"
    "output:\n"
    "  type: string\n"
    "  description: ...\n"
    "'''\n"
    "mentor.submit_display(\"RBSCHOOSER2_SIGNATURE\", sig_yaml)"
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
        "Explain it briefly, then express the signature as YAML with this shape:\n\n"
        "name: <function name>\n"
        "inputs:\n"
        "  - name: <input name>\n"
        "    type: <type or structure>\n"
        "    description: <one sentence>\n"
        "output:\n"
        "  type: <type or structure>\n"
        "  description: <one sentence>\n\n"
        "Return ONLY YAML."
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
    if isinstance(answer, dict):
        return True, "ok"
    if not isinstance(answer, str):
        return False, "Expected JSON text (string) or a Python dict."
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

    if isinstance(answer, dict):
        return False, "Submit YAML text (not a Python dict). Paste the YAML Gemini returned.", {}

    s = _strip_code_fences(str(answer))
    if len(s.strip()) < 40:
        return False, "This looks too short to be a meaningful signature. Paste the full YAML block.", {"chars": len(s.strip())}

    try:
        import yaml
        obj = yaml.safe_load(s)
        if not isinstance(obj, dict):
            return False, "YAML did not parse as an object. Paste the YAML block Gemini returned.", {}
        for k in ["name", "inputs", "output"]:
            if k not in obj:
                return False, f"Missing required key: {k}", {}
        if not isinstance(obj.get("name"), str) or not obj["name"].strip():
            return False, "`name` must be a non-empty string.", {}
        if not isinstance(obj.get("inputs"), list) or len(obj["inputs"]) < 1:
            return False, "`inputs` must be a non-empty list.", {}
        if not isinstance(obj.get("output"), dict):
            return False, "`output` must be an object with at least type and description.", {}
        state["rbschooser2_signature"] = obj
        return True, "Signature recorded.", {
            "name": obj.get("name"),
            "n_inputs": len(obj.get("inputs", [])) if isinstance(obj.get("inputs"), list) else 0,
            "output_keys": sorted(list(obj.get("output", {}).keys())) if isinstance(obj.get("output"), dict) else [],
        }
    except Exception:
        lower = s.lower()
        if "name:" not in lower or "inputs:" not in lower or "output:" not in lower:
            return False, "I did not see the required YAML keys (name, inputs, output). Paste the YAML Gemini returned.", {}
        state["rbschooser2_signature_yaml"] = s
        return True, "Signature recorded.", {"chars": len(s)}
