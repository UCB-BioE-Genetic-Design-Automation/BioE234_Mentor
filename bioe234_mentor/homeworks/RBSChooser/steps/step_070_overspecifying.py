from __future__ import annotations

from typing import Any, Dict, Tuple
import re


STEP_ID = "070"
KEY = "OVERSPECIFYING"
TITLE = "Detection puzzle: overspecifying a prompt"
NEXT_STEP = None
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
    if not isinstance(answer, dict):
        return False, "Submit a dict with keys 'choice' and 'code'."
    if "choice" not in answer or "code" not in answer:
        return False, "Your dict must include keys 'choice' and 'code'."
    choice = answer.get("choice")
    code = answer.get("code")
    if not isinstance(choice, str) or not choice.strip():
        return False, "'choice' must be a non-empty string."
    if not isinstance(code, str) or not code.strip():
        return False, "'code' must be a non-empty string containing the source of `choose_rbs`."
    return True, ""


VALID_CHOICES = [
    "It adds an extra ATG by putting ATG in the returned RBS.",
    "It duplicates the start codon when you concatenate rbs + cds.",
    "It hardcodes ATG into the returned RBS sequence.",
    "It returns an initiation region, not an upstream-only RBS.",
    "It forces ATGATG at the junction when you do rbs + cds.",
]


def validate(answer: Dict[str, Any], state: Dict[str, Any]):
    choice = str(answer.get("choice", "")).strip()
    code = str(answer.get("code", "")).strip()

    if choice not in VALID_CHOICES:
        return False, "That is not the issue we are targeting for the deterministic downstream failure.", {}

    # Basic sanity checks for the pasted code.
    if "def choose_rbs" not in code:
        return False, "Paste the full function definition starting with `def choose_rbs(cds: str) -> str:`.", {}

    # Execute in a minimal namespace.
    ns: Dict[str, Any] = {}
    try:
        compiled = compile(code, "student_choose_rbs.py", "exec")
        exec(compiled, ns, ns)
    except Exception as e:
        return False, f"I could not run the code you pasted ({type(e).__name__}: {e}).", {}

    fn = ns.get("choose_rbs")
    if not callable(fn):
        return False, "I did not find a callable `choose_rbs` in the pasted code.", {}

    # Deterministic, testable failure condition:
    # cds begins with ATG. The bad prompt pushes ATG into the returned RBS, which
    # produces ATGATG at the junction when concatenated.
    test_cds = "ATG" + "GCT" * 20
    try:
        rbs = fn(test_cds)
    except Exception as e:
        return False, f"Your choose_rbs raised an exception on a test CDS ({type(e).__name__}: {e}).", {}

    if not isinstance(rbs, str):
        return False, "choose_rbs must return a string.", {}
    rbs = rbs.strip().upper()
    if not re.fullmatch(r"[ACGT]+", rbs or ""):
        return False, "choose_rbs must return DNA letters only (A/C/G/T).", {}

    combined = rbs + test_cds
    junction = combined[max(0, len(rbs) - 6) : len(rbs) + 6]

    expected = combined[len(rbs) - 3 : len(rbs) + 3] if len(rbs) >= 3 else ""
    if not (rbs.endswith("ATG") and expected == "ATGATG"):
        return False, (
            "For this step, your pasted code should reflect the bad prompt and create a duplicated start codon "
            "when concatenated as rbs + cds (junction contains ATGATG). "
            "It did not. Make sure you defined `choose_rbs` using Gemini's output from the bad prompt, and that the submission captured its source correctly."
        ), {
            "rbs_end": rbs[-12:],
            "junction_snippet": junction,
        }

    return True, (
        "Nice. You found the failure mode the prompt is trying to bait.\n\n"
        "Now do a quick experiment (no submission needed).\n"
        "Go back to Gemini and reuse the same prompt, but remove the instruction that says to include ATG in the returned RBS.\n"
        "If you leave that instruction out, the model will usually default to returning an upstream-only RBS (no extra start codon).\n\n"
        "Optional: also try replacing 'Use a 7-nucleotide spacer' with 'Use the correctly-sized spacer'.\n"
        "This makes the instruction abstract, so the model will inject what it believes is the correct spacing.\n\n"
        "After Gemini responds, ask: 'What spacer length did you pick, and why?'\n"
        "Notice how removing a constraint can sometimes produce a more informed and correct result than a mistaken, overspecified instruction.\n"
        "If you are not sure what the right value is, define it abstractly and ask the model to choose and explain its choice."
    ), {
        "rbs_len": len(rbs),
        "rbs_end": rbs[-12:],
        "junction_snippet": junction,
    }


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
        "<b>After defining <code>choose_rbs</code> in this notebook, answer the question below.</b><br>"
        "Your submission will automatically capture the source of <code>choose_rbs</code> from the notebook."
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
            f"mentor.submit_display({key!r}, {{'choice': {chosen_text!r}, 'code': __import__('inspect').getsource(choose_rbs)}})"
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
