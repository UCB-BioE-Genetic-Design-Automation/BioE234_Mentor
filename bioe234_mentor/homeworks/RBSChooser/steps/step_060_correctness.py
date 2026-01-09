

STEP_ID = "060"
KEY = "CORRECTNESS_DIAGNOSIS"
TITLE = "Correctness"
NEXT_STEP = "DONE"
HASH_MODE = "json"

SUBMIT_STUB = 'mentor.submit_display("CORRECTNESS_DIAGNOSIS", "missing_spacer")'


_CHOICES = [
    (
        "missing_spacer",
        "Returns only an SD motif. When you build rbs + cds there is no spacer, so SD-to-start spacing is wrong.",
        "ok",
    ),
    (
        "non_deterministic",
        "Uses randomness, so you might get different SD motifs across runs.",
        "True, but non-determinism is not the fundamental correctness problem here. Even if you always returned the same SD, returning only an SD motif is not a usable RBS in the intended rbs + cds assembly.",
    ),
    (
        "ignores_cds",
        "The function takes cds but does not use it.",
        "This is a design smell, but it is not the core reason rbs + cds fails. The main issue is that the output is only an SD motif with no spacer, so it cannot place the SD at a meaningful distance from the start codon.",
    ),
    (
        "sd_is_not_enough",
        "An RBS is more than the SD motif; you need sequence context so the ribosome can initiate correctly.",
        "Close, but be specific about what is wrong in this usage. The key failure is that rbs + cds gives no defined SD-to-start spacing because only the SD motif is returned.",
    ),
    (
        "needs_promoter",
        "The design failed because there was no promoter.",
        "A promoter is required for expression in general, but this step is about what is wrong with the choose_rbs logic itself when used as rbs + cds.",
    ),
    (
        "needs_terminator",
        "The design failed because there was no terminator.",
        "A terminator can matter, but it is not the fundamental issue in this toy algorithm. The toy algorithm fails at the RBS level in the rbs + cds assembly.",
    ),
    (
        "wrong_start_codon",
        "The start codon was not AUG.",
        "The CDS here starts with ATG by construction. The failure is that the algorithm does not produce a usable upstream region that positions the SD relative to the start.",
    ),
    (
        "secondary_structure",
        "mRNA secondary structure might hide the SD or start codon.",
        "Secondary structure is a real factor, but you do not even get to that level yet. The algorithm output lacks basic geometry for initiation because it returns only an SD motif and no spacer.",
    ),
    (
        "s1_au_rich",
        "The upstream region should be AU-rich to help S1 binding.",
        "That can matter in some contexts, but it is not the basic failure mode here. The output is only an SD motif and cannot define SD-to-start spacing in rbs + cds.",
    ),
    (
        "wrong_orientation",
        "The RBS needs to be downstream of the CDS.",
        "No. The RBS is upstream of the start codon. The problem is not orientation, it is that the algorithm returns only an SD motif with no spacer.",
    ),
    (
        "spacing_too_far",
        "The SD is too far from the start codon.",
        "In this assembly it is the opposite. The SD sits immediately adjacent to the CDS because no spacer is provided.",
    ),
    (
        "spacing_too_close",
        "The SD is too close to the start codon.",
        "This is getting at the core issue, but the best diagnosis names the structural cause: returning only the SD motif gives no spacer, so the SD-to-start spacing is wrong.",
    ),
    (
        "sd_sequence_wrong",
        "AGGAGG is not the right SD sequence.",
        "AGGAGG is a common SD-like motif in E. coli examples. The issue here is not the exact letters, it is that the algorithm returns only the motif and omits the spacer needed for initiation geometry.",
    ),
    (
        "host_specific",
        "Different hosts use different RBS rules.",
        "Host context can matter, but even in a friendly host the output here is not a usable upstream RBS region in the rbs + cds assembly because it provides no spacer.",
    ),
    (
        "codon_usage",
        "GFP might not express due to codon usage.",
        "Codon usage affects elongation, but this step is about translation initiation logic. The toy algorithm fails before that because the SD is not positioned relative to the start codon.",
    ),
    (
        "plasmid_copy_number",
        "The plasmid copy number was too low.",
        "Copy number affects expression level, but it does not explain a systematic failure of an RBS design algorithm. The failure here is that the algorithm output is not structurally compatible with rbs + cds.",
    ),
    (
        "no_rna_pol",
        "The construct did not express because RNA polymerase was missing.",
        "This is not a meaningful diagnosis for the algorithm. Assume the cell is normal. The question is what is wrong with the RBS selection logic when used as rbs + cds.",
    ),
    (
        "seed_random",
        "It would work if you set random.seed.",
        "Setting a seed makes outputs repeatable, but it does not fix correctness. Even a repeatable SD-only output would still lack a spacer and fail the intended assembly.",
    ),
    (
        "needs_rbs_calculator",
        "You must use the RBS Calculator to get expression.",
        "Design tools can help, but the failure here is more basic: the algorithm does not even construct an upstream region with a spacer that positions the SD relative to the start.",
    ),
    (
        "gfp_wrong",
        "GFP did not express because GFP is not fluorescent.",
        "GFP is fluorescent when expressed and folded. The setup is that the construct did not express. The issue is in the initiation logic of the algorithm.",
    ),
]

_CORRECT_ID = "missing_spacer"


def render(state) -> str:
    choices_lines = []
    for cid, short, _why in _CHOICES:
        choices_lines.append(f"- {cid}: {short}")

    return (
        "A student team used this algorithm to design an RBS upstream of GFP, but the colonies did not turn green.\n\n"
        "They used the RBS chooser output by concatenating it directly to the CDS, like this:\n\n"
        "```python\n"
        "rbs = choose_rbs(cds)\n"
        "assembled = rbs + cds\n"
        "```\n\n"
        "Here is the algorithm they used:\n\n"
        "```python\n"
        "import random\n\n"
        "def choose_rbs(cds: str) -> str:\n"
        "    sds = [\"AGGAGG\", \"AAGGAG\", \"GGAGGA\"]\n"
        "    return random.choice(sds)\n"
        "```\n\n"
        "There is something fundamentally wrong with the logic, given the intended use rbs + cds.\n\n"
        "Discuss the algorithm and the rbs + cds result with Gemini, then choose the best explanation from the list below.\n\n"
        "Choices:\n"
        + "\n".join(choices_lines)
        + "\n"
    )


def shape_check(answer):
    if not isinstance(answer, str):
        return False, "Expected a string ID from the list of choices."
    s = answer.strip()
    if not s:
        return False, "Submission was empty."
    return True, "ok"


def validate(answer, state):
    s = str(answer).strip()
    valid = {cid for cid, _short, _why in _CHOICES}

    if s not in valid:
        sample = ", ".join(sorted(list(valid))[:8])
        return False, f"Unrecognized choice. Submit one of the choice IDs (for example: {sample}).", {}

    if s != _CORRECT_ID:
        why = next((w for cid, _short, w in _CHOICES if cid == s), "Not correct.")
        return False, why, {"chosen": s}

    state["correctness_diagnosis"] = s
    return True, "Correct.", {"chosen": s}