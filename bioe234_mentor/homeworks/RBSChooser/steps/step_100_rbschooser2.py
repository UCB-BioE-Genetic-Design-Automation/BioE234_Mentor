from __future__ import annotations

from typing import Any, Dict, Tuple


STEP_ID = "100"
KEY = "RBSCHOOSER2"
TITLE = "Build RBSChooser2"
NEXT_STEP = "110"
HASH_MODE = "callable"

# Student submits the class object after following the prompt.
SUBMIT_STUB = "mentor.submit_display('RBSCHOOSER2', RBSChooser2)"


def _load_prompt_text() -> str:
    """Load tools/prompt.txt from the installed package.

    This step uses the prompt as a static artifact in the repo.
    """
    # Prefer importlib.resources so it works when installed as a package.
    try:
        from importlib import resources

        pkg = "bioe234_mentor.homeworks.RBSChooser.tools"
        return resources.files(pkg).joinpath("prompt.txt").read_text(encoding="utf-8")
    except Exception:
        # Fallback to relative path (useful during local dev).
        from pathlib import Path

        tools_path = Path(__file__).resolve().parents[1] / "tools" / "prompt.txt"
        return tools_path.read_text(encoding="utf-8")


def render(state: Dict[str, Any]) -> str:
    return (
        "Paste the prompt into your LLM of choice, and follow its guidance to build the class in this notebook.\n\n"
        "Use the Copy for Gemini button below to copy the full prompt to your clipboard.\n\n"
        "When you have defined the `RBSChooser2` class in this notebook, submit the class object.\n\n"
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
    return True, "Thanks. Next we will test and refine your implementation one step at a time.", {}


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
