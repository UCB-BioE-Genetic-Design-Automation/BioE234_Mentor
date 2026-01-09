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
    "Discuss choose_rbs and the rbs + cds result with Gemini, then choose the best explanation using the picker below."
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
    return PROMPT


def gui(state, mentor=None) -> None:
    from bioe234_mentor.multiple_choice import display_mcq_widget

    display_mcq_widget(
        key=KEY,
        valid=VALID,
        invalid=INVALID,
        prompt="### Multiple choice\n\nPick the best explanation, then click **Check**.",
        n_total=5,
        n_valid=1,
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
            return False, why, {"chosen": s}

    return False, "Please submit the exact text of the correct explanation.", {"chosen": s}