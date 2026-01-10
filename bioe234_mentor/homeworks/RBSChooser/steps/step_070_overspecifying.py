from __future__ import annotations

from typing import Any, Dict, Tuple
import re


STEP_ID = "070"
KEY = "OVERSPECIFYING"
TITLE = "Detection puzzle: overspecifying a prompt"
NEXT_STEP = "080"
HASH_MODE = "json"

# The student is expected to paste this into Gemini, then paste the generated code
# into a new code cell in the same Colab notebook and observe the downstream failure.
#
# Subtle (but important) wrong instruction:
# - It tells Gemini to INCLUDE ATG in the returned RBS. Most pipelines concatenate
#   rbs + cds where cds already starts with ATG, producing ATGATG at the junction.
#
# The prompt includes plausible spacing language; the autograde check focuses on the deterministic junction bug.
BAD_PROMPT = '''Implement this function exactly (do not change name or signature):


def choose_rbs(cds: str) -> str:
    """
    Given a CDS (DNA sequence string), return an RBS (DNA sequence string) to place immediately upstream.
    """

Constraints:
- `cds` is a DNA sequence string (A/C/G/T).
- Return a single DNA string only (A/C/G/T). No explanations.
- Deterministic for the same `cds`.

Biology and formatting requirements (follow exactly):
1. Use the canonical E. coli Shine-Dalgarno motif `AGGAGG`.
2. Use a 7-nucleotide spacer between the end of the Shine-Dalgarno motif and the start codon.
3. Treat the returned “RBS” as the whole translation-initiation region, so it must include the start codon `ATG` at the end.
4. Choose the spacer deterministically from the CDS GC content:
   - if GC fraction of `cds` is >= 0.50, use spacer `GC`
   - otherwise use spacer `AT`

So the return value must be: `AGGAGG` + spacer + `ATG`.

Please output only the Python code for `choose_rbs` (imports allowed), nothing else.'''


def render(state: Dict[str, Any]) -> str:
    return (
        "You are about to use an intentionally bad prompt.\n\n"
        "1) Copy the prompt below into your existing Gemini chat and let it generate a `choose_rbs` function.\n"
        "2) Paste Gemini's returned `def choose_rbs(cds: str) -> str:` into a NEW code cell in this Colab and run it.\n"
        "3) Run the function on a test CDS and look at the output.\n"
        "4) Paste the output back into Gemini and ask: 'What is wrong with this output biologically, and what was wrong with my prompt?'\n\n"
        "Bad prompt (copy everything):\n"
        "```text\n"
        + BAD_PROMPT
        + "\n```\n\n"
    )


def shape_check(answer: Any) -> Tuple[bool, str]:
    if not isinstance(answer, str) or not answer.strip():
        return False, "Submit a non-empty string (your chosen option text)."
    return True, ""


VALID_CHOICES = [
    "It adds an extra ATG by putting ATG in the returned RBS.",
    "It duplicates the start codon when you concatenate rbs + cds.",
    "It hardcodes ATG into the returned RBS sequence.",
    "It returns an initiation region, not an upstream-only RBS.",
    "It forces ATGATG at the junction when you do rbs + cds.",
]


def validate(answer: Any, state: Dict[str, Any]):
    choice = str(answer).strip()

    if choice not in VALID_CHOICES:
        return False, "That is not the issue we are targeting for the deterministic downstream failure.", {}

    return True, "Correct.", {}


def gui(state: Dict[str, Any], mentor) -> None:
    """GUI: student answers the MCQ after defining choose_rbs in the notebook."""
    try:
        import ipywidgets as widgets
        from IPython.display import HTML, display
    except Exception:
        # Fallback: if widgets are unavailable, the step can still be completed via submit_display.
        return

    from bioe234_mentor.multiple_choice import display_mcq_widget

    intro = HTML(
        "<div style='margin:0 0 10px 0;'>"
        "<b>Answer the multiple-choice question below.</b><br>"
        "After you get it right, the next step will appear. The copied line also includes optional comments you can try."
        "</div>"
    )

    display(intro)

    quiz_prompt = (
        "Detection puzzle: the prompt above is subtly wrong. "
        "Which instruction is the main problem and causes a deterministic downstream failure when someone later builds the full sequence as rbs + cds?"
    )

    valid = VALID_CHOICES

    invalid = [
        (
            "AGGAGG is the wrong Shine-Dalgarno sequence here.",
            "AGGAGG is a common Shine-Dalgarno motif; this is not the key issue here.",
        ),
        (
            "GC fraction is undefined, so the spacer rule cannot work.",
            "GC fraction is easy to compute. The bigger issue is what the prompt forces into the returned string.",
        ),
        (
            "Requiring determinism is the problem with this prompt.",
            "Determinism is not the issue. The failure is about what gets concatenated at the junction.",
        ),
        (
            "Asking for code-only output is the problem here.",
            "That is a formatting request, not the biological logic bug.",
        ),
        (
            "Using a fixed spacer length is the main biological error.",
            "That is suspicious, but the deterministic failure we are checking is caused by a different instruction.",
        ),
        (
            "It should use RNA bases (U) instead of DNA (T).",
            "RBS sequences are typically written as DNA in this homework context. This is not what causes the deterministic junction bug.",
        ),
        (
            "It should ask for the reverse complement of the RBS.",
            "No reverse complement is needed for this task. The failure we are targeting is a duplicated start codon at the junction.",
        ),
        (
            "The Shine-Dalgarno should be AAGGAG, not AGGAGG.",
            "There are many plausible SD-like motifs. The key deterministic failure here is about duplicating ATG when concatenating rbs + cds.",
        ),
        (
            "It should explicitly require uppercase output only.",
            "Case normalization is not the issue. The deterministic failure is created by including ATG inside the returned RBS.",
        ),
        (
            "It should validate that the CDS starts with ATG first.",
            "Even if you validated the CDS, including ATG in the returned RBS still creates a duplicated ATG when the CDS already begins with ATG.",
        ),
    ]

    def submit_call_builder(key: str, chosen_text: str) -> str:
        return (
            f"mentor.submit_display({key!r}, {chosen_text!r})\n"
            "# Optional: try fixing the prompt (no submission needed).\n"
            "# In Gemini, reuse the same prompt, but replace the instruction about including ATG with:\n"
            "#   Treat the returned \"RBS\" as the Shine-Dalgarno and spacer only.\n"
            "# This keeps the start codon inside the CDS, so rbs + cds does not duplicate ATG.\n"
            "#\n"
            "# Also optional: replace 'Use a 7-nucleotide spacer' with 'Use the correctly-sized spacer'.\n"
            "# After Gemini responds, ask: 'What spacer length did you pick, and why?'\n"
            "# Notice how removing a constraint can produce a more informed result than a mistaken, overspecified instruction.\n"
        )

    def gemini_prompt_builder(_: str) -> str:
        return (
            "I used the following prompt to get code for choose_rbs(cds: str) -> str, "
            "but my pipeline later concatenates full_sequence = rbs + cds where cds already starts with ATG.\n\n"
            "Here is the exact prompt I used:\n\n"
            + BAD_PROMPT
            + "\n\nIn 2 to 4 sentences, identify what is wrong with the prompt and what failure it causes downstream. "
            "Be specific about what shows up at the junction when I do rbs + cds."
        )

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
