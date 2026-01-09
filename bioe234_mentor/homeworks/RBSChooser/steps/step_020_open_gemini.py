STEP_ID = "020"
KEY = "GEMINI_READY"
TITLE = "Open Gemini"
NEXT_STEP = "030"
HASH_MODE = "json"
SUBMIT_STUB = 'mentor.submit_display("GEMINI_READY", "ready")'


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
        "For the next steps, you will use Gemini AI in a separate browser tab to help you write code in this notebook.\n\n"
        "Open Gemini AI here (sign in if needed):\n"
        "https://gemini.google.com/app\n\n"
        "Once it is open and you are ready to continue, submit `ready`."
    )


def shape_check(answer):
    if not isinstance(answer, str):
        return False, "Expected a string."
    s = answer.strip().lower()
    if s != "ready":
        return False, "Submit exactly: ready"
    return True, "ok"


def validate(answer, state):
    passcode = (state.get("passcode") or "").strip()
    if not passcode:
        return False, "Passcode is missing. Go back and submit your passcode first.", {}
    state["gemini_ready_at"] = "set"
    return True, "Gemini is open. Proceeding.", {}