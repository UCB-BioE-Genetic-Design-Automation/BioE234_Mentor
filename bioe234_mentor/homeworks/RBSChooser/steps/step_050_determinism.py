STEP_ID = "050"
KEY = "IS_DETERMINISTIC"
TITLE = "Determinism"
NEXT_STEP = "060"
HASH_MODE = "json"

SUBMIT_STUB = (
    "mentor.submit_display(\"IS_DETERMINISTIC\", is_deterministic)"
)


def render(state) -> str:
    return (
        "Determinism means: if you call a function twice with the same input, you get the same output both times.\n\n"
        "Determinism matters for debugging and testing. If outputs change unpredictably, it becomes hard to reproduce bugs and hard to write reliable tests.\n\n"
        "Consider this function:\n\n"
        "```python\n"
        "import random\n\n"
        "def choose_rbs(cds: str) -> str:\n"
        "    sds = [\"AGGAGG\", \"AAGGAG\", \"GGAGGA\"]\n"
        "    return random.choice(sds)\n"
        "```\n\n"
        "Your task is to decide whether `choose_rbs` is deterministic, using two approaches.\n\n"
        "1) Ask Gemini (reasoning)\n"
        "In your Gemini chat, ask:\n\n"
        "```text\n"
        "Is this function deterministic? Explain why or why not.\n"
        "```\n\n"
        "2) Ask Gemini for runnable Colab code (evidence)\n"
        "In the same Gemini chat, ask Gemini to write code you can run in this Colab notebook that:\n"
        "- defines the function exactly as shown above\n"
        "- makes an example `cds` string (any DNA sequence is fine)\n"
        "- calls `choose_rbs(cds)` twice\n"
        "- compares the two outputs and stores the result in a variable named `is_deterministic` (a boolean)\n\n"
        "After you run that code cell, submit the value of `is_deterministic`.\n\n"
        "Expected outcome: because the function randomly selects among three SD sequences, `is_deterministic` should be False."
    )


def shape_check(answer):
    if isinstance(answer, bool):
        return True, "ok"
    if isinstance(answer, str) and answer.strip():
        return True, "ok"
    return False, "Submit a boolean (True/False) or a non-empty string like False."


def validate(answer, state):
    val = None

    if isinstance(answer, bool):
        val = answer
    elif isinstance(answer, str):
        s = answer.strip().lower()
        if s in {"false", "f", "no"}:
            val = False
        elif s in {"true", "t", "yes"}:
            val = True
        else:
            return False, "Submit True or False (or the string 'False').", {}
    else:
        return False, "Submit True or False.", {}

    if val is not False:
        return False, "For this function, the correct answer is False. Re-check by running it twice on the same input.", {}

    state["is_deterministic"] = False

    return True, "Recorded.", {"is_deterministic": False}
