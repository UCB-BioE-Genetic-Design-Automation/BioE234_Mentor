import re

STEP_ID = "020"
KEY = "GEMINI_URL"
TITLE = "Open Gemini and paste your chat URL"
NEXT_STEP = "030"
HASH_MODE = "json"
SUBMIT_STUB = 'mentor.submit_display("GEMINI_URL", "https://gemini.google.com/app/<id>")'

_GEMINI_URL_RE = re.compile(r"^https://gemini\.google\.com/app/[0-9a-fA-F]{16,64}(?:[?#].*)?$")


def render(state) -> str:
    passcode = (state.get("passcode") or "").strip()
    if not passcode:
        return (
            "I do not have your passcode on record, so I cannot continue.\n\n"
            "Go back and submit your passcode first using:\n\n"
            "```python\nmentor.submit_display(\"PASSCODE\", \"<your_passcode>\")\n```\n\n"
            "Then run `mentor.display()` to return here."
        )

    return (
        f"Passcode recorded: '{passcode}'.\n\n"
        "For the next steps, you will use Gemini in a separate browser tab to help you write code in this notebook.\n\n"
        "1) Open Gemini:\n"
        "https://gemini.google.com/app\n\n"
        "2) Start a new chat (or open the chat you will use for this tutorial).\n\n"
        "3) Copy the URL from your browser address bar. It should look like:\n\n"
        "https://gemini.google.com/app/###\n\n"
        "Paste your Gemini chat URL here.\n\n"
        "Also, share this Colab notebook with:\n"
        "- jcanderson@berkeley.edu\n"
        "- javadamn@berkeley.edu\n"
        "(Read-only is fine: share with Viewer access.)"
    )


def shape_check(answer):
    if not isinstance(answer, str):
        return False, "Expected a URL string."
    s = answer.strip()
    if not s:
        return False, "URL was empty."
    if " " in s:
        return False, "URL contains spaces. Paste the URL exactly."
    return True, "ok"


def validate(answer, state):
    passcode = (state.get("passcode") or "").strip()
    if not passcode:
        return False, "Passcode is missing. Go back and submit your passcode first.", {}

    s = str(answer).strip()
    if _GEMINI_URL_RE.fullmatch(s) is None:
        return (
            False,
            "That does not look like a Gemini chat URL. Paste a URL like https://gemini.google.com/app/<id> from your browser address bar.",
            {},
        )

    state["gemini_url"] = s
    state["gemini_ready_at"] = "set"

    return True, "Gemini URL recorded. Proceeding.", {"gemini_url": s}