import re

STEP_ID = "020"
KEY = "COLAB_URL"
TITLE = "Share your Colab notebook URL"
NEXT_STEP = "030"
HASH_MODE = "json"
SUBMIT_STUB = 'mentor.submit("COLAB_URL", "<paste_colab_url>")'

_COLAB_DRIVE_URL_RE = re.compile(r"^https://colab\.research\.google\.com/drive/[A-Za-z0-9_-]{20,}(?:\?.*)?(?:#.*)?$")
_COLAB_SHORT_MSG = "Paste a Colab Drive URL like https://colab.research.google.com/drive/<id>"


def render(state) -> str:
    passcode = state.get("passcode")
    if passcode:
        first = f"I stored your passcode '{passcode}'.\n\n"
    else:
        first = "I stored your passcode.\n\n"

    return (
        first
        + "Using an LLM to code is a powerful way to quickly generate new functionality. Like all tools, there are many things you need to be aware of about its behavior to get good results.\n\n"
        + "Open a new Google Colab notebook. Title it **RBSChooser2_Tutorial**. Then submit the notebook URL here.\n\n"
        + "If you are unsure how to do any of the tasks I ask you to perform, copy the request into the LLM and ask it how to do it."
    )


def shape_check(answer):
    if not isinstance(answer, str):
        return False, "Expected a URL string."
    s = answer.strip()
    if not s:
        return False, "URL was empty."
    if " " in s:
        return False, "URL contains spaces. Paste the URL exactly."
    if _COLAB_DRIVE_URL_RE.fullmatch(s) is None:
        return False, _COLAB_SHORT_MSG
    return True, "ok"


def validate(answer, state):
    s = str(answer).strip()

    if _COLAB_DRIVE_URL_RE.fullmatch(s) is None:
        return False, _COLAB_SHORT_MSG, {}

    state["colab_url"] = s

    return True, "Colab URL recorded.", {"colab_url": s}