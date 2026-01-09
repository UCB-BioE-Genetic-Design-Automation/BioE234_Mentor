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
    "choose_rbs returns only a Shine-Dalgarno motif, not the spacer between the SD and the start codon, so rbs + cds has no defined initiation geometry.",
    "The output is just an SD sequence. Without an explicit spacer, concatenating rbs + cds leaves the SD at the wrong distance from the start codon.",
    "It selects an SD motif but never positions it relative to the start codon; the missing spacer means rbs + cds cannot encode aligned SD-to-start spacing.",
    "An RBS design must include SD plus a spacer region. Returning only the motif omits the key distance constraint needed for initiation when assembled as rbs + cds.",
    "The algorithm never constructs the SD-to-start interval, so the returned 'rbs' is incomplete; rbs + cds produces undefined spacing and poor initiation.",
]

INVALID = [
    (
        "Because choose_rbs uses randomness, two runs may yield different sequences, which can confuse debugging and reproducibility of GFP expression results.",
        "True, but randomness is not the fundamental correctness issue in the rbs + cds assembly. Even a fixed SD-only output would still be structurally incompatible with the intended use.",
    ),
    (
        "The function accepts cds but does not use it, so it cannot account for downstream context effects and will output an RBS that is incompatible with GFP specifically.",
        "Not using cds is a design smell, but it is not the core failure in the rbs + cds assembly. The basic issue is that the output omits the spacer needed to position the SD relative to the start codon.",
    ),
    (
        "AGGAGG is not the correct Shine-Dalgarno sequence for E. coli, so the ribosome will not bind effectively and translation initiation will fail regardless of spacing.",
        "AGGAGG is a common SD-like motif in E. coli examples. The issue here is not the exact letters; it is that the algorithm returns only the motif and omits the spacer needed for initiation geometry.",
    ),
    (
        "The GFP construct likely failed due to promoter strength or plasmid copy number; the RBS algorithm could be fine but expression is too low to see.",
        "Copy number and promoter strength affect expression level, but they do not explain a systematic failure of an RBS design algorithm. The failure here is that the algorithm output is not structurally compatible with rbs + cds.",
    ),
    (
        "Secondary structure in the 5' UTR could hide the SD and prevent binding; the algorithm needs folding analysis, not changes to how it builds the RBS.",
        "Secondary structure can matter, but you do not even get to that level yet. The algorithm output lacks basic initiation geometry because it returns only an SD motif and no spacer.",
    ),
]

SUBMIT_STUB = None


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