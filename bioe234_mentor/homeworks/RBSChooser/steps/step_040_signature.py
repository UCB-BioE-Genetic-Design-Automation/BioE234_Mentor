import json
import re

STEP_ID = "040"
KEY = "RBSCHOOSER2_SIGNATURE"
TITLE = "Identify the function signature"
NEXT_STEP = "DONE"
HASH_MODE = "json"
SUBMIT_STUB = (
    "sig_json = r'''{\n"
    "  \"name\": \"RBSChooser2\",\n"
    "  \"inputs\": [\n"
    "    {\"name\": \"dna\", \"type\": \"string\", \"description\": \"...\"}\n"
    "  ],\n"
    "  \"output\": {\"type\": \"string\", \"description\": \"...\"}\n"
    "}'''\n"
    "mentor.submit_display(\"RBSCHOOSER2_SIGNATURE\", sig_json)"
)


def render(state) -> str:
    code = (state.get("rbschooser2_code") or "").strip()
    if not code:
        return (
            "I do not have your generated code on record, so I cannot continue.\n\n"
            "Go back and submit your draft function code first. Then run `mentor.display()` to return here."
        )

    lines = code.splitlines()
    preview = "\n".join(lines[:25])
    if len(lines) > 25:
        preview += "\n..."

    prompt = (
        "You are looking at a function signature. A signature is the interface of a function: \n"
        "- the function name\n"
        "- the inputs it accepts (names and expected types/structure)\n"
        "- the output it returns (type/structure)\n\n"
        "The important point: the signature is arbitrary. Gemini chose it. Different choices imply different ways a user must call the function.\n\n"
        "Ask yourself: Did it ask for a DNA string? A numeric strength? A list of sequences?\n"
        "What does it return: a string, a number, a dict/object, or a more complex structure?\n\n"
        "In Gemini, ask for the signature and request a formal JSON description you can submit.\n\n"
        "Use this prompt in Gemini (paste your function code where indicated):\n\n"
        "---\n"
        "Given the following Python function, identify its signature (name, inputs, output).\n"
        "Return ONLY a JSON object with this shape:\n"
        "{\n"
        "  \"name\": <string>,\n"
        "  \"inputs\": [ {\"name\": <string>, \"type\": <string>, \"description\": <string>} , ... ],\n"
        "  \"output\": {\"type\": <string>, \"description\": <string>}\n"
        "}\n\n"
        "Function code:\n"
        "```python\n"
        + preview
        + "\n```\n"
        "---\n\n"
        "Then paste the JSON you get back here and submit it."
    )

    return prompt


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

    obj = None

    if isinstance(answer, dict):
        obj = answer
    else:
        s = _strip_code_fences(str(answer))
        if len(s) < 20:
            return False, "This looks too short to be a meaningful signature. Paste the full JSON object.", {"chars": len(s)}
        try:
            obj = json.loads(s)
        except Exception:
            return False, "I could not parse this as JSON. Paste the JSON object Gemini returned.", {}

    if not isinstance(obj, dict):
        return False, "Parsed value was not a JSON object. Paste a JSON object with keys name, inputs, output.", {}

    for k in ["name", "inputs", "output"]:
        if k not in obj:
            return False, f"Missing required key: {k}", {}

    if not isinstance(obj.get("name"), str) or not obj["name"].strip():
        return False, "`name` must be a non-empty string.", {}

    if not isinstance(obj.get("inputs"), list) or len(obj["inputs"]) < 1:
        return False, "`inputs` must be a non-empty list.", {}

    if not isinstance(obj.get("output"), dict):
        return False, "`output` must be an object with at least a type and description.", {}

    state["rbschooser2_signature"] = obj

    return True, "Signature recorded.", {
        "name": obj.get("name"),
        "n_inputs": len(obj.get("inputs", [])) if isinstance(obj.get("inputs"), list) else 0,
        "output_keys": sorted(list(obj.get("output", {}).keys())) if isinstance(obj.get("output"), dict) else [],
    }
