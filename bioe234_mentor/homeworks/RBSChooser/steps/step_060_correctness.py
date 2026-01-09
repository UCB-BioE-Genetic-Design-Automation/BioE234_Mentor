

from __future__ import annotations

STEP_ID = "060"
KEY = "CORRECTNESS_DIAGNOSIS"
TITLE = "Correctness"
NEXT_STEP = "070"
HASH_MODE = "json"

PROMPT = (
    "A student team used choose_rbs to design an RBS upstream of GFP, but the colonies did not turn green.\n\n"
    "They used the result by concatenating it directly to the CDS, like this: rbs + cds.\n\n"
    "There is something fundamentally wrong with the logic, given that intended use.\n\n"
    "Discuss choose_rbs and the rbs + cds result with Gemini, then choose the best explanation."
)

VALID = [
    "The algorithm returns only an SD motif and no spacer, so rbs + cds cannot place the SD at a meaningful distance from the start codon.",
    "The output is just an SD sequence. Without a spacer, concatenating rbs + cds gives the wrong SD to start geometry.",
    "It picks an SD motif but never builds the spacer, so the SD is not positioned relative to the start codon in rbs + cds.",
    "Returning only an SD motif is not enough. The design needs SD plus spacer so assembly places the SD about 5 to 6 nt upstream of the start.",
    "The algorithm does not create the region between the SD and the start codon, so rbs + cds yields no defined SD to start spacing.",
]

INVALID = [
    (
        "It uses randomness, so you might get different motifs across runs.",
        "True, but randomness is not the fundamental correctness issue in the rbs + cds assembly. Even a fixed SD only output would still be structurally incompatible with the intended use.",
    ),
    (
        "The function takes cds but does not use it, so the output is wrong.",
        "Not using cds is a design smell, but it is not the core failure in the rbs + cds assembly. The basic issue is that the output omits the spacer needed to position the SD relative to the start codon.",
    ),
    (
        "AGGAGG is not the right Shine Dalgarno sequence, so translation will fail.",
        "AGGAGG is a common SD like motif in E. coli examples. The issue here is not the exact letters, it is that the algorithm returns only the motif and omits the spacer needed for initiation geometry.",
    ),
    (
        "The plasmid copy number was too low, so GFP did not express.",
        "Copy number affects expression level, but it does not explain a systematic failure of an RBS design algorithm. The failure here is that the algorithm output is not structurally compatible with rbs + cds.",
    ),
    (
        "mRNA secondary structure might hide the SD, so it does not express.",
        "Secondary structure can matter, but you do not even get to that level yet. The algorithm output lacks basic geometry for initiation because it returns only an SD motif and no spacer.",
    ),
]

SUBMIT_STUB = 'mentor.submit_display("CORRECTNESS_DIAGNOSIS", "' + VALID[0] + '")'


def render(state) -> str:
    from bioe234_mentor.multiple_choice import make_quiz

    quiz = make_quiz(
        prompt=PROMPT,
        valid=VALID,
        invalid=INVALID,
        n_total=5,
        n_valid=1,
    )

    options = [o.text for o in quiz.options]

    feedback = state.pop("last_incorrect_060", None)
    feedback_block = ""
    if isinstance(feedback, dict) and feedback.get("why"):
        feedback_block = (
            "\n\n---\n\n"
            "### Feedback from your last attempt\n\n"
            + str(feedback.get("why"))
            + "\n"
        )

    gui_snippet = (
        "from bioe234_mentor.multiple_choice import display_mcq_widget\n"
        "from bioe234_mentor.homeworks.RBSChooser.steps import step_060_correctness as s\n\n"
        "display_mcq_widget(\n"
        "    key=s.KEY,\n"
        "    valid=s.VALID,\n"
        "    invalid=s.INVALID,\n"
        "    prompt=s.PROMPT,\n"
        ")\n"
    )

    lines = [f"{i}) {t}" for i, t in enumerate(options, start=1)]

    return (
        PROMPT
        + "\n\n"
        + "You can do this in either of two ways.\n\n"
        + "1) Recommended: run the optional GUI picker below. It will reveal the exact submit call when you pick the correct explanation.\n\n"
        + "```python\n"
        + gui_snippet
        + "```\n\n"
        + "2) Manual: pick the best explanation from the list below and submit it exactly as written.\n\n"
        + "Choices:\n\n"
        + "\n\n".join(lines)
        + "\n\n"
        + "Submit the exact text of the best choice."
        + feedback_block
    )


def shape_check(answer):
    if isinstance(answer, str) and answer.strip():
        return True, "ok"
    return False, "Submit a non-empty string."


def validate(answer, state):
    s = str(answer).strip()

    if s in VALID:
        state["correctness_diagnosis"] = "missing_spacer"
        return True, "Correct.", {"chosen": s}

    for t, why in INVALID:
        if s == t:
            state["last_incorrect_060"] = {"why": why}
            return False, why, {"chosen": s}

    state["last_incorrect_060"] = {
        "why": "I did not recognize that response. Please submit one of the choices exactly as written."
    }
    return False, "Unrecognized response.", {"chosen": s}