import ast
import re

STEP_ID = "030"
KEY = "RBSCHOOSER2_CODE"
TITLE = "Ask Gemini for a first draft"
NEXT_STEP = "040"
HASH_MODE = "json"
SUBMIT_STUB = "rbs_code = r'''<paste the full Python function here>'''\nmentor.submit_display(\"RBSCHOOSER2_CODE\", rbs_code)"

_PROMPT = "Write a function to choose an RBS for a gene"


def render(state) -> str:
    passcode = (state.get("passcode") or "").strip()
    if not passcode:
        return (
            "I do not have your passcode on record, so I cannot continue.\n\n"
            "Go back and submit your passcode first using:\n\n"
            "```python\nmentor.submit_display(\"PASSCODE\", \"<your_passcode>\")\n```\n\n"
            "Then run:\n\n"
            "```python\nmentor.display()\n```\n\n"
            "to return here."
        )

    return (
        f"Open a new Gemini chat in your browser.\n\n"
        "In that new chat, type this exact prompt:\n\n"

        "Gemini will respond with code. Copy the full Python function it gives you.\n\n"
        "```python\n"
        "\"{_PROMPT}\""
        "```\n\n"

        "Paste only the Python function code. Do not paste your prompt."
    )


def shape_check(answer):
    if not isinstance(answer, str):
        return False, "Expected a string containing Python code."
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
    passcode = (state.get("passcode") or "").strip()
    if not passcode:
        return False, "Passcode is missing. Go back and submit your passcode first.", {}

    raw = str(answer)
    s = _strip_code_fences(raw)

    if s.strip() == _PROMPT:
        return False, "You pasted the prompt. Paste the Python function code Gemini produced.", {}

    if len(s.strip()) < 150:
        return False, "This looks too short. Paste the full function code (starting with def ...).", {"chars": len(s.strip())}

    if "def " not in s:
        return False, "I did not see a Python function definition. Paste the code starting with def ....", {}

    try:
        tree = ast.parse(s)
    except SyntaxError as e:
        return False, f"This does not parse as Python. Paste only the function code. (SyntaxError: {e.msg})", {}

    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not funcs:
        return False, "I did not find any def function in what you pasted. Paste the full function code.", {}

    names = [f.name for f in funcs]

    state["rbschooser2_code"] = s

    return True, "Draft code recorded.", {"chars": len(s), "functions": names}
