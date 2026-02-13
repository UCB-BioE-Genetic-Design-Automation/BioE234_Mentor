from __future__ import annotations

from typing import Any, Dict, Tuple


STEP_ID = "100"
KEY = "RBSCHOOSER2"
TITLE = "Build RBSChooser2"
NEXT_STEP = "DONE"
HASH_MODE = "callable"


# Student submits the class object after following the prompt.
SUBMIT_STUB = "mentor.submit_display('RBSCHOOSER2', RBSChooser2)"

# Last-resort fallback in case prompt.txt was not included in the installed package.
# Keep tools/prompt.txt as the source of truth during development.
FALLBACK_PROMPT_TEXT = """You are a tutoring LLM embedded in a BioE234 Mentor assignment workflow. The instructor is delegating to you the task of delivering a guided tutorial to a student.

Your mission is to guide the student through designing and implementing an algorithm (RBSChooser) in small, checkable increments. You must be interactive and must not dump a full finished solution in one message.

Audience: undergraduate or early graduate bioengineering student writing Python.
Tone: direct, patient, concrete.

---

## Student runtime environment (given)
The student will work in a Colab notebook (or equivalent) and will have:

```python
from bioe234_mentor.mentor import Mentor
mentor = Mentor.load_or_create("RBSChooser")

# Helper tools provided for this assignment:
from bioe234_mentor.homeworks.RBSChooser.tools import (
    translate,
    edit_distance,
    hairpin_counter,
)
```

These helpers are provided for the assignment (the student should use them rather than reimplement them):
- `translate(cds: str) -> str`  (DNA coding sequence to amino acids)
- `edit_distance(a: str, b: str) -> int`
- `hairpin_counter(seq: str) -> int`

The student must write their own helper function that computes the first six amino acids from an input CDS by using `translate(cds)`.

RBSOption is defined as:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RBSOption:
    utr: str
    cds: str
    gene_name: str
    first_six_aas: str
```

Do not ask the student for an RBSOption definition.

---

## Source data (what the student is given in the notebook)
Before the student writes their own code, the notebook will download two data files into the runtime.

Expected files:
- `sequence.gb` (GenBank genome annotation for E. coli K12 MG1655)
- `511145-WHOLE_ORGANISM-integrated.txt` (proteomics abundance table for MG1655 from PAX-db)

What each file is used for:
- The proteomics file is used to empirically identify strongly expressed genes (top 5 percent by gene count, ranked by abundance).
- The GenBank file is used to extract, for each gene: locus tag (join key), gene name, CDS sequence, and a 5' UTR sequence (a short region upstream of the CDS start, taking strand into account).

How to recognize correct files:
- GenBank (`sequence.gb`) should begin with a `LOCUS` line and contain an `ORIGIN` section. In this assignment’s file, the first 10 bases of the genome sequence at `ORIGIN` are `AGCTTTTCAT` (the next bases continue `TCTGACTGCA...`).
- Proteomics (`511145-WHOLE_ORGANISM-integrated.txt`) begins with metadata lines starting with `#` and then has a two-column table whose header includes `string_external_id` and `abundance` (often the first column header is `#string_external_id`), followed by rows like `511145.b0002\t498` (tab-delimited; abundance may be an integer or a float).

The student must upload these two files to you in the chat so you can confirm filenames, readability, and structure before any coding.

---

## Function lifecycle and caching (initiate vs run)
RBSChooser is a function-as-object pattern:

- `initiate()` runs once. It loads the raw data files, performs preprocessing, and builds a cached list of candidate options.
- `run(cds, ignores)` runs many times. It selects a single RBSOption for an input CDS using the cached options.

The student should confirm `initiate()` is correct before writing `run()` by inspecting the cached variables produced by `initiate()`.

---

## The assignment tasks (what the student must build)
The student must implement RBSChooser in two parts.

### Part A: initiate (build the candidate RBSOption list)
The student must implement `initiate()` so it:

1) Reads the GenBank file and extracts per-gene information needed to build options.
2) Reads the proteomics file and prunes it to the top 5 percent most abundant genes (top 5 percent by number of genes).
3) Merges the two datasets by locus tag, keeping only genes in the top 5 percent.
   - Note: proteomics IDs look like `511145.b0002`, but GenBank locus tags look like `b0002`. In initiate, normalize proteomics IDs by splitting on `.` and keeping the final token before joining.
4) Constructs RBSOption instances and stores them in a cached class variable (for example `self.options` or `RBSChooser.options`).

For each RBSOption:
- `utr` is the 5' UTR sequence extracted for that source gene.
  - Default UTR rule for this assignment: use 50 nt immediately upstream of the CDS start on the coding strand; if the CDS is on the minus strand, use 50 nt downstream and then reverse-complement to produce the coding-strand 5' UTR.
- `cds` is the CDS for that source gene.
- `gene_name` is the gene identifier for debugging.
- `first_six_aas` is computed once for the source gene using `translate(source_cds)` and stored.

### Part B: run (choose one option for an input CDS)
The student must implement a method or standalone function that:

- Inputs:
  - `cds: str` (an input DNA coding sequence)
  - `ignores: set[RBSOption]` (options to avoid returning)
- Output:
  - one chosen `RBSOption` instance from the cached collection created in `initiate()`

Selection must be based on three criteria:

1) Exclusion: never return an option that is in `ignores`.
2) Secondary structure occlusion: prefer options with less predicted secondary-structure interaction between the option UTR and the input CDS near the start. You must guide the student to define exactly what window to score and why.
3) Peptide similarity: prefer options whose source gene is more similar to the input CDS in the early peptide sequence. Use `RBSOption.first_six_aas` compared to the student’s computed first six amino acids for the input CDS.

This is multi-objective. You must guide the student to choose a deterministic strategy (lexicographic ranking, weighted score, Pareto with deterministic tie-break, etc.) and justify it briefly.

Determinism requirements:
- Same inputs must always return the same `RBSOption`.
- If the returned option is added to `ignores` and the chooser is called again, it must return a different option (if any remain).
- If no valid options remain after exclusions, raise a clear exception.

---

## Persistent outline requirement
You must maintain a persistent outline of the tutorial plan so the student can redirect you back to it.

You are responsible for storing it.
- If you have a built-in persistent document feature (for example Canvas, Notes, or any similar persistent workspace), create a document titled “RBSChooser Outline” and save the outline there.
- If you can store a persistent note/file in the environment (for example a Keep-style note or a saved text document), do that.
- If no persistent storage is available, you must still treat the outline as persistent: keep it as a stable internal reference and be ready to restate it on request.

Do not ask the student to save or manage the outline.

If either of you gets off course, the student should say: “Read your stored outline,” and you must immediately restate the outline and resume from the current step.

---

## First assistant message to the student (must be sent verbatim)
Send the following message as your very first reply to the student.
- Do not add any preface or explanation.
- Do not wrap it in quotes.
- Do not include any labels or markers.
- Preserve the numbering exactly as written.

I am here to help you write RBSChooser. We will go through the following together. If we get off course, tell me: “Read your stored outline.”

I will store our outline in my persistent notes as “RBSChooser Outline.” You do not need to store anything.

Stored outline (keep this numbering):

0) Upload the two data files so I can confirm their filenames and structure.
1) Cell: Imports, Mentor setup, and quick sanity checks for provided helper tools.
2) Cell: Explain the initiate vs run lifecycle in your own words, then inspect the starter scaffold (what functions exist and what is missing).
3) Cell: Parse GenBank into a gene info mapping keyed by locus tag (gene name, CDS, and a candidate 5' UTR sequence).
4) Cell: Parse proteomics abundance data into a mapping keyed by locus tag, then prune to the top 5 percent.
5) Cell: Merge proteomics top 5 percent with gene info (keep only high-expression locus tags).
6) Cell: Construct a list of RBSOption objects from the merged data and store it as a cached class variable.
7) Cell: Write a small initiate test that prints counts and a few example options so you can sanity check.
8) Cell: Write `first_six_aas(cds: str) -> str` using `translate(cds)` with careful edge-case handling.
9) Cell: Define CDS validation rules used by your chooser (what to accept, what to reject) and implement `validate_cds(cds: str) -> str` or equivalent.
10) Cell: Define the occlusion scoring window and implement `occlusion_score(utr: str, cds: str) -> int` using `hairpin_counter`.
11) Cell: Implement peptide similarity scoring `peptide_distance(opt_first_six: str, input_first_six: str) -> int` using `edit_distance`.
12) Cell: Choose a deterministic multi-objective strategy and implement `option_rank(opt, input_first_six, cds) -> tuple` (or an explicit weighted score) with a deterministic tie-break.
13) Cell: Implement `run(cds, ignores) -> RBSOption` (filter ignores, score all candidates, select best, raise on none).
14) Cell: Write tests that verify determinism, ignores behavior, and failure mode.
15) Cell: Assemble `RBSChooser2` as a clean, commented, readable final version (the full solution in one place), then submit it for grading with `mentor.submit_display(\"RBSCHOOSER2\", RBSChooser2)`.

Let’s get started.

Step 0: Please upload the two downloaded files now:
- sequence.gb
- 511145-WHOLE_ORGANISM-integrated.txt

---

## Colab organization requirement
Each outline line that starts with “Cell:” corresponds to exactly one Colab code cell the student will write.

---

## After the first message: file check, then quiz
After the student uploads the files requested in the first message, you must do the following before any coding:

1) Verify the files.
- Confirm you received exactly two files.
- Confirm their filenames match the expected names. If they do not, tell the student what you received and what you expected, and instruct them to rename or re-upload.
- Confirm the GenBank file begins with `LOCUS` and contains `ORIGIN`, and that the sequence at ORIGIN begins with `AGCTTTTCAT`.
- Confirm the proteomics file contains a header with `string_external_id` and `abundance` (possibly `#string_external_id`), and rows that look like `511145.b####` with numeric abundances (int or float).
- If anything looks wrong, stop and help the student fix it.

2) Initiate/run comprehension check (brief).
Ask the student to answer:
- What is the job of initiate?
- What is the job of run?

Then evaluate their answers. If anything is missing or incorrect, ask targeted follow-ups until you are satisfied.

3) Confirm workflow agreement.
Tell the student you have already stored the outline and you will use it to keep the session on track. Ask them to confirm they will follow the “one cell per outline step” structure.
Do not ask the student whether they stored the outline or where it is stored.

Only then proceed to Cell 1. At the end (Cell 15), you will submit your final `RBSChooser2` class using `mentor.submit_display(\"RBSCHOOSER2\", RBSChooser2)`; that will run the autograder tests and produce the final report text you will copy into bCourses.
"""



def _load_prompt_text() -> str:
    """Load tools/prompt.txt.

    Priority order:
    1) Packaged resource (works when prompt.txt is included as package data).
    2) Local repo path relative to this step file.
    3) Local repo path relative to the current working directory.
    4) Embedded fallback text (last resort).
    """
    # 1) importlib.resources (preferred when packaged correctly)
    try:
        from importlib import resources

        pkg = "bioe234_mentor.homeworks.RBSChooser.tools"
        return resources.files(pkg).joinpath("prompt.txt").read_text(encoding="utf-8")
    except Exception:
        pass

    # 2) Relative to this file (useful in editable installs)
    try:
        from pathlib import Path

        tools_path = Path(__file__).resolve().parents[1] / "tools" / "prompt.txt"
        if tools_path.exists():
            return tools_path.read_text(encoding="utf-8")
    except Exception:
        pass

    # 3) Relative to CWD (useful when running from the repo root)
    try:
        from pathlib import Path

        cwd = Path.cwd().resolve()
        rel = Path("bioe234_mentor/homeworks/RBSChooser/tools/prompt.txt")
        for base in (cwd, *cwd.parents):
            candidate = base / rel
            if candidate.exists():
                return candidate.read_text(encoding="utf-8")
    except Exception:
        pass

    # 4) Last resort
    return FALLBACK_PROMPT_TEXT


def render(state: Dict[str, Any]) -> str:
    return (
        "Open a new chat with your LLM of choice. Starting fresh lets you control what context the model sees. "
        "If you continue an older chat, unrelated examples and even bad algorithms can leak in and steer the model in the wrong direction. "
        "Unless the old context is essential, use a new chat as a blank slate.\n"
        "Use the Copy for Gemini button below to copy the full prompt to your clipboard.\n"
        "Paste the prompt and then follow its guidance to build RBSChooser2\n\n"
        "When you have defined the `RBSChooser2` class in this notebook, submit it as.\n\n"
        "Submission:\n"
        "```python\n"
        "mentor.submit_display('RBSCHOOSER2', RBSChooser2)\n"
        "```"
    )


def shape_check(answer: Any) -> Tuple[bool, str]:
    # The student should submit the class object.
    if answer is None:
        return False, "Submit the RBSChooser2 class object (not a string)."

    if not isinstance(answer, type):
        return False, "Submit the class object itself, e.g. mentor.submit_display('RBSCHOOSER2', RBSChooser2)"

    if getattr(answer, "__name__", None) != "RBSChooser2":
        return False, "Submit the class named RBSChooser2."

    # Minimal interface expectations.
    for attr in ("initiate", "run"):
        if not hasattr(answer, attr):
            return False, f"Your RBSChooser2 class must define a `{attr}()` method."

    return True, ""


def validate(answer: Any, state: Dict[str, Any]):
    import inspect
    import time
    import traceback
    from types import ModuleType

    report: Dict[str, Any] = {
        "tests": [],
        "timing": {},
        "notes": [],
        "exceptions": {},
    }

    def add_test(name: str, ok: bool, details: str = "", **extra: Any) -> None:
        item: Dict[str, Any] = {"name": name, "ok": bool(ok)}
        if details:
            item["details"] = details
        item.update(extra)
        report["tests"].append(item)

    def add_exception(name: str, e: Exception) -> None:
        report["exceptions"][name] = {
            "type": type(e).__name__,
            "message": str(e),
            "traceback": "".join(traceback.format_exc(limit=20)),
        }

    def _get_runner(cls_obj):
        try:
            runner = cls_obj()  # prefer instance methods
            return runner, "instance"
        except Exception:
            # Fall back to classmode (some students may write @classmethod style)
            return cls_obj, "class"

    def _call_initiate(runner):
        fn = getattr(runner, "initiate")
        try:
            return fn()
        except TypeError:
            return fn(runner)

    def _call_run(runner, cds: str, ignores: Any):
        fn = getattr(runner, "run")

        # Try common call shapes.
        for attempt in (
            lambda: fn(cds, ignores),
            lambda: fn(cds),
            lambda: fn(cds=cds, ignores=ignores),
            lambda: fn(cds=cds),
        ):
            try:
                return attempt()
            except TypeError:
                pass

        # Last resort: attempt to bind signature and call.
        sig = inspect.signature(fn)
        kwargs: Dict[str, Any] = {}
        for pname, _param in sig.parameters.items():
            if pname in ("self", "cls"):
                continue
            if pname.lower() == "cds":
                kwargs[pname] = cds
            elif pname.lower() == "ignores":
                kwargs[pname] = ignores
        return fn(**kwargs)

    def _looks_like_option(obj: Any) -> bool:
        for attr in ("utr", "cds", "gene_name", "first_six_aas"):
            if not hasattr(obj, attr):
                return False
        return True

    def _first_six_aas(cds: str) -> str:
        from bioe234_mentor.homeworks.RBSChooser.tools import translate

        aa = translate(cds)
        return aa[:6]

    def _try_get_options(runner, initiate_ret: Any):
        if isinstance(initiate_ret, list) and initiate_ret:
            return initiate_ret

        for name in ("options", "candidate_options", "candidates"):
            if hasattr(runner, name):
                val = getattr(runner, name)
                if isinstance(val, list) and val:
                    return val

        cls_obj = runner if isinstance(runner, type) else type(runner)
        for name in ("options", "candidate_options", "candidates"):
            if hasattr(cls_obj, name):
                val = getattr(cls_obj, name)
                if isinstance(val, list) and val:
                    return val

        return None

    def _instrument_hairpin_counter(runner):
        stats: Dict[str, Any] = {"calls": 0, "seq_lens": []}

        run_attr = getattr(runner, "run")
        base_func = getattr(run_attr, "__func__", run_attr)
        g = getattr(base_func, "__globals__", {})

        patches = []

        def make_wrapper(original):
            def wrapped(seq: str):
                stats["calls"] += 1
                try:
                    stats["seq_lens"].append(len(seq))
                except Exception:
                    pass
                return original(seq)

            try:
                wrapped.__name__ = getattr(original, "__name__", "hairpin_counter")
            except Exception:
                pass
            return wrapped

        for k, v in list(g.items()):
            if callable(v) and getattr(v, "__name__", "") == "hairpin_counter":
                wrapper = make_wrapper(v)
                g[k] = wrapper
                patches.append((g, k, v))

        for k, v in list(g.items()):
            if isinstance(v, ModuleType) and hasattr(v, "hairpin_counter"):
                orig = getattr(v, "hairpin_counter")
                if callable(orig) and getattr(orig, "__name__", "") == "hairpin_counter":
                    wrapper = make_wrapper(orig)
                    setattr(v, "hairpin_counter", wrapper)
                    patches.append((v, "hairpin_counter", orig))

        return stats, patches

    def _restore_patches(patches):
        for container, key, original in patches:
            try:
                if isinstance(container, dict):
                    container[key] = original
                else:
                    setattr(container, key, original)
            except Exception:
                pass

    # --- Begin checks ---
    runner, mode = _get_runner(answer)
    add_test("instantiate", True, f"Runner mode: {mode}")

    initiate_ret = None
    options = None
    initiate_ok = False

    # 1) initiate
    t0 = time.perf_counter()
    try:
        initiate_ret = _call_initiate(runner)
        initiate_ok = True
        t1 = time.perf_counter()
        report["timing"]["initiate_s"] = round(t1 - t0, 6)
        add_test("initiate_runs", True, f"initiate completed in {report['timing']['initiate_s']} s")
    except Exception as e:
        t1 = time.perf_counter()
        report["timing"]["initiate_s"] = round(t1 - t0, 6)
        add_test("initiate_runs", False, f"initiate raised: {type(e).__name__}: {e}")
        add_exception("initiate", e)
        # Provide targeted hints that do not assume a specific implementation.
        report["notes"].extend(
            [
                "If initiate() reads files, confirm these two filenames exist in the Colab runtime: sequence.gb and 511145-WHOLE_ORGANISM-integrated.txt.",
                "If your code uses absolute paths or local machine paths, replace them with just the filenames (Colab working directory).",
                "If initiate() builds candidates, it must end with a non-empty list stored on self.options (or returned as a list).",
            ]
        )

    # 2) options discovery (only if initiate succeeded)
    if initiate_ok:
        options = _try_get_options(runner, initiate_ret)
        if options is None:
            add_test(
                "options_present",
                False,
                "Could not find a non-empty options list (return from initiate or attribute like self.options).",
            )
            report["notes"].append("Make sure initiate() builds and stores a list of RBSOption candidates.")
        else:
            add_test("options_present", True, f"Found {len(options)} candidate options.", n_options=len(options))
            sample = options[:3]
            ok_struct = all(_looks_like_option(o) for o in sample)
            add_test("option_shape", ok_struct, "Options should have utr, cds, gene_name, first_six_aas")

    # 3) Prepare test CDS variants
    base_cds = "ATG" + "GCT" + "GCT" + "GCT" + "GCT" + "GCT" + "GCT" + ("GCT" * 10)
    silent_cds = "ATG" + "GCC" + base_cds[6:]
    missense_cds = "ATG" + "ACT" + base_cds[6:]

    try:
        aa_base = _first_six_aas(base_cds)
        aa_silent = _first_six_aas(silent_cds)
        aa_missense = _first_six_aas(missense_cds)
        add_test(
            "peptide_probe_setup",
            True,
            "Computed first six AAs for base, silent, missense.",
            aa_base=aa_base,
            aa_silent=aa_silent,
            aa_missense=aa_missense,
        )
    except Exception as e:
        add_test("peptide_probe_setup", False, f"translate probe raised: {type(e).__name__}: {e}")
        add_exception("translate_probe", e)
        report["notes"].append("The provided translate(cds) helper should be importable. If you shadowed it, rename your function.")

    # 4) Try run at least once (even if initiate failed) so we can give a useful note.
    hairpin_stats = {"calls": 0, "seq_lens": []}
    patches = []
    try:
        try:
            hairpin_stats, patches = _instrument_hairpin_counter(runner)
        except Exception as e:
            # If instrumentation fails, we still try to call run and report.
            add_test("hairpin_instrument", False, f"Could not instrument hairpin_counter: {type(e).__name__}: {e}")
            add_exception("hairpin_instrument", e)

        # Determinism and basic run execution
        ignores_empty = set()
        t_runs = []
        outputs = []

        for _ in range(5):
            t0 = time.perf_counter()
            out = _call_run(runner, base_cds, ignores_empty)
            t1 = time.perf_counter()
            t_runs.append(t1 - t0)
            outputs.append(out)

        add_test("run_executes", True, "run executed successfully on a basic input.")
        report["timing"]["run_mean_s"] = round(sum(t_runs) / max(1, len(t_runs)), 6)

        out0 = outputs[0]
        add_test("run_returns_option", _looks_like_option(out0), "run should return an RBSOption-like object")

        def _opt_id(o: Any) -> Tuple[Any, Any, Any, Any]:
            try:
                return (getattr(o, "gene_name"), getattr(o, "utr"), getattr(o, "cds"), getattr(o, "first_six_aas"))
            except Exception:
                return (repr(o), None, None, None)

        ids = [_opt_id(o) for o in outputs]
        deterministic = all(i == ids[0] for i in ids)
        add_test("determinism", deterministic, "Same input should return the same option 5 times.")

        # ignores behavior
        ignores_ok = False
        ignores_detail = ""
        try:
            opt1 = _call_run(runner, base_cds, set())
            try:
                ignores1 = {opt1}
            except TypeError:
                ignores1 = None

            if ignores1 is None:
                ignores_ok = False
                ignores_detail = "Returned option is not hashable, so it cannot be placed into a set for ignores."
            else:
                opt2 = _call_run(runner, base_cds, ignores1)
                ignores_ok = _opt_id(opt2) != _opt_id(opt1)
                ignores_detail = (
                    "Second call returned a different option when the first was ignored."
                    if ignores_ok
                    else "Second call returned the same option even though it was ignored."
                )
        except Exception as e:
            ignores_ok = False
            ignores_detail = f"ignores test raised: {type(e).__name__}: {e}"
            add_exception("ignores_test", e)

        add_test("ignores", ignores_ok, ignores_detail)

    except Exception as e:
        add_test("run_executes", False, f"run raised: {type(e).__name__}: {e}")
        add_exception("run", e)
        if not initiate_ok:
            report["notes"].append("run() failed because initiate() did not complete. Fix initiate() first, then resubmit.")
        else:
            report["notes"].append("Fix run() so it can execute on a basic CDS input.")
    finally:
        _restore_patches(patches)

    # 5) Hairpin counter evidence (only meaningful if run executed)
    calls = int(hairpin_stats.get("calls", 0))
    lens = hairpin_stats.get("seq_lens", [])
    if calls > 0:
        add_test(
            "hairpin_counter_used",
            True,
            f"hairpin_counter called {calls} times.",
            calls=calls,
            seq_len_min=min(lens) if lens else None,
            seq_len_max=max(lens) if lens else None,
        )
    else:
        # Only treat as a hard fail if run executed successfully.
        run_ok = {t["name"]: t["ok"] for t in report["tests"]}.get("run_executes", False)
        add_test("hairpin_counter_used", bool(not run_ok), "No evidence that hairpin_counter was called during run().")
        if run_ok:
            report["notes"].append("The prompt expects run() to use hairpin_counter to score occlusion near the junction.")

    # Overall decision
    required = {
        "initiate_runs": True,
        "options_present": True,
        "run_executes": True,
        "run_returns_option": True,
        "determinism": True,
        "ignores": True,
        "hairpin_counter_used": True,
    }

    results = {t["name"]: t["ok"] for t in report["tests"]}
    hard_fail = [name for name, want in required.items() if want and not results.get(name, False)]

    # Message to the student
    lines = []
    lines.append("RBSChooser2 automated check report")
    lines.append("")

    for t in report["tests"]:
        mark = "OK" if t["ok"] else "FAIL"
        line = f"- {mark}: {t['name']}"
        if t.get("details"):
            line += f"  ({t['details']})"
        lines.append(line)

    lines.append("")
    if report["timing"]:
        lines.append("Timing")
        for k, v in report["timing"].items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    if report["notes"]:
        lines.append("Notes")
        for n in report["notes"]:
            lines.append(f"- {n}")
        lines.append("")

    if report.get("exceptions"):
        lines.append("Exceptions")
        for name, info in report["exceptions"].items():
            lines.append(f"- {name}: {info.get('type')}: {info.get('message')}")
        lines.append("")

    if hard_fail:
        lines.append("Status")
        lines.append("- Not done yet. Fix the failed items above, then resubmit your class.")
        return False, "\n".join(lines), report

    lines.append("Status")
    lines.append("- Looks good enough to proceed to the next step.")
    return True, "\n".join(lines), report


def gui(state: Dict[str, Any], mentor) -> None:
    """Display a copy button for prompt.txt plus an optional preview."""
    try:
        import json

        import ipywidgets as widgets
        from IPython.display import HTML, Javascript, display
    except Exception:
        return

    prompt_text = _load_prompt_text()

    header = HTML(
        "<div style='margin:0 0 8px 0;'>"
        "<b>Copy the prompt and paste it into Gemini.</b> "
        "(Build the class in Colab, then submit it.)"
        "</div>"
    )
    display(header)

    copy_btn = widgets.Button(description="Copy for Gemini", button_style="")
    status = widgets.HTML("<span></span>")

    def _copy(_):
        # Use the browser clipboard.
        js = (
            "navigator.clipboard.writeText(" + json.dumps(prompt_text) + ")"
            ".then(() => { console.log('copied'); })"
            ".catch((e) => { console.log('copy failed', e); });"
        )
        display(Javascript(js))
        status.value = "<span style='color:#2b7;'>Copied.</span>"

    copy_btn.on_click(_copy)
    display(widgets.HBox([copy_btn, status]))

    # Optional preview for students who want to scroll it here.
    preview = widgets.Textarea(
        value=prompt_text,
        description="Prompt",
        layout=widgets.Layout(width="100%", height="260px"),
        disabled=True,
    )

    accordion = widgets.Accordion(children=[preview])
    accordion.set_title(0, "Preview prompt (optional)")
    display(accordion)

    return None
