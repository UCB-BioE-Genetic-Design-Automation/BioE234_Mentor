from __future__ import annotations

from typing import Any, Dict, Tuple


STEP_ID = "080"
KEY = "LOGIC_SANITY"
TITLE = "Logic sanity checks"
# NOTE: set to the real next step when it exists.
NEXT_STEP = "100"
HASH_MODE = "json"

# Placeholder code the student will critique.
# Replace this with the actual minimal rbschooser solution once ready.
EXAMPLE_CODE = """# Minimal (intentionally simplistic) RBS chooser for critique in Step 080.
# Contract: return an upstream-only RBS sequence (Shine-Dalgarno + spacer). No start codon.


def choose_rbs(cds: str) -> str:
    cds = cds.strip().upper()

    shine_dalgarno = "AGGAGG"

    # Heuristic spacer selection based on GC fraction.
    gc = (cds.count("G") + cds.count("C")) / len(cds)
    spacer = "ATATATA" if gc >= 0.50 else "AAAAAAA"  # 7 nt spacer

    return shine_dalgarno + spacer
"""

# Prompt students paste into the LLM (Gemini) to generate a critique.
LLM_PROMPT = """I will paste a minimal implementation of:
- choose_rbs(cds: str) -> str

Task context:
- cds is a DNA sequence string (A/C/G/T). In our pipeline, we build full_sequence = rbs + cds.
- choose_rbs should return an upstream-only RBS sequence (Shine-Dalgarno + spacer). It should NOT include the start codon.
- Output must be DNA letters only (A/C/G/T) and deterministic.

Please do the following:
1) List exactly 10 things that are wrong or risky about this implementation.
2) Keep each item short (one sentence).
3) Only critique logic, assumptions, and failure modes. Do not comment on style.

CODE START
{code}
CODE END
"""


def render(state: Dict[str, Any]) -> str:
    return (
        "In this step, you will practice reading code critically.\n\n"
        "1) Copy the code below into your notebook (or just read it).\n"
        "2) Copy the prompt below into your existing Gemini chat.\n"
        "3) Gemini will list 10 issues.\n"
        "4) Then answer the multiple-choice question: which issue did Gemini NOT mention?\n\n"
        "Example code (placeholder):\n"
        "```python\n" + EXAMPLE_CODE + "\n```\n\n"
        "Prompt for Gemini (copy everything):\n"
        "```text\n" + LLM_PROMPT.format(code=EXAMPLE_CODE) + "\n```\n"
    )


# These 5 are the correct answers for this MCQ: items the LLM did NOT mention.
# Placeholders for now. Replace later.
VALID_CHOICES = [
    "It can crash on empty CDS due to division by zero.",
    "It hardcodes AGGAGG, ignoring host and gene-specific SD needs.",
    "It ignores RNA secondary structure that can block translation initiation.",
    "It fixes spacer length at 7 even when optimal spacing varies.",
    "It uses an arbitrary 50% GC cutoff with no clear basis.",
]


def shape_check(answer: Any) -> Tuple[bool, str]:
    if not isinstance(answer, str) or not answer.strip():
        return False, "Submit a non-empty string (your chosen option text)."
    return True, ""


def validate(answer: Any, state: Dict[str, Any]):
    choice = str(answer).strip()

    if choice not in VALID_CHOICES:
        return False, "That was mentioned by the LLM (or is not one of the intended answers).", {}

    return True, "Correct.", {}


def gui(state: Dict[str, Any], mentor) -> None:
    """MCQ: choose the issue the LLM did NOT mention."""
    try:
        from IPython.display import HTML, display
    except Exception:
        return

    from bioe234_mentor.multiple_choice import display_mcq_widget

    intro = HTML(
        "<div style='margin:0 0 10px 0;'>"
        "<b>Question:</b> Which issue did the LLM <i>not</i> mention as a problem with the algorithm?"
        "</div>"
    )
    display(intro)

    quiz_prompt = (
        "Which of the following issues did the LLM NOT say was wrong with this algorithm?"
    )

    valid = VALID_CHOICES

    # These 10 are wrong answers for this MCQ (placeholders): items the LLM DID mention.
    # Each tuple is (option_text, feedback).
    invalid = [
        ("It is deterministic for the same CDS input every time.", "This is already true of the code shown."),
        ("It returns a DNA string made only from A, C, G, and T.", "This is already true of the code shown."),
        ("It uppercases the CDS first, reducing case-related surprises.", "This is already true of the code shown."),
        ("It strips whitespace from the CDS before doing any counting.", "This is already true of the code shown."),
        ("It returns an upstream-only RBS and does not add a start codon.", "This is already true of the code shown."),
        ("It always returns a plain string, not a list or dictionary.", "This is already true of the code shown."),
        ("It uses a Shine-Dalgarno motif followed by a spacer sequence.", "This is already true of the code shown."),
        ("It always uses a seven-nucleotide spacer for consistent spacing.", "This is already true of the code shown."),
        ("It computes GC fraction directly from the CDS using counts.", "This is already true of the code shown."),
        ("It uses no randomness, external tools, or hidden state.", "This is already true of the code shown."),
    ]

    def submit_call_builder(key: str, chosen_text: str) -> str:
        return f"mentor.submit_display({key!r}, {chosen_text!r})"

    def gemini_prompt_builder(_: str) -> str:
        # Cheater button should copy the critique prompt only (no options).
        return LLM_PROMPT.format(code=EXAMPLE_CODE)

    display_mcq_widget(
        key=KEY,
        valid=valid,
        invalid=invalid,
        prompt=quiz_prompt,
        n_total=5,
        n_valid=1,
        seed=None,
        submit_call_builder=submit_call_builder,
        state=state,
        state_key=STEP_ID,
        gemini_prompt_builder=gemini_prompt_builder,
        show_gemini_after_wrong_attempts=2,
    )

    return None
