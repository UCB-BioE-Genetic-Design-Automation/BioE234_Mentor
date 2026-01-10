from __future__ import annotations

"""Multiple-choice widgets for Colab.

This module provides small helpers for rendering randomized multiple-choice questions
using ipywidgets.

The main entry point is `display_mcq_widget`, which shows a prompt and a set of
choices, grades a selection, and can optionally persist interaction state if a
`state` dict is provided.

This module is homework-agnostic. Step- or homework-specific prompts should be
provided by the caller (for example, by passing a prompt string or a callback).
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
import random
import html
import uuid
import time
import threading


@dataclass(frozen=True)
class MCQOption:
    text: str
    is_correct: bool
    why_incorrect: Optional[str] = None


@dataclass(frozen=True)
class MCQQuiz:
    prompt: str
    options: Tuple[MCQOption, ...]

    def correct_texts(self) -> Tuple[str, ...]:
        return tuple(o.text for o in self.options if o.is_correct)

    def why_map(self) -> Dict[str, str]:
        m: Dict[str, str] = {}
        for o in self.options:
            if (not o.is_correct) and o.why_incorrect:
                m[o.text] = o.why_incorrect
        return m


def make_quiz(
    *,
    prompt: str,
    valid: Sequence[str],
    invalid: Sequence[Tuple[str, str]],
    n_total: int = 5,
    n_valid: int = 1,
    seed: Optional[int] = None,
) -> MCQQuiz:
    """Create a randomized multiple-choice quiz.

    Args:
        prompt: Text shown above the choices.
        valid: A sequence of correct answer strings.
        invalid: A sequence of (decoy_text, why_incorrect) pairs.
        n_total: Total number of options to display.
        n_valid: Number of correct options to include.
        seed: Optional RNG seed for reproducibility.

    Returns:
        MCQQuiz with shuffled options.

    Notes:
        - This function is homework-agnostic.
        - Callers are responsible for providing prompt/choices.
    """
    if not valid:
        raise ValueError("valid must be non-empty")
    if n_total < 2:
        raise ValueError("n_total must be at least 2")
    if n_valid < 1 or n_valid > n_total:
        raise ValueError("n_valid must be between 1 and n_total")
    if len(invalid) < (n_total - n_valid):
        raise ValueError("invalid must contain at least n_total - n_valid items")

    rng = random.Random(seed)

    if n_valid > len(valid):
        raise ValueError("n_valid cannot exceed len(valid)")

    correct_texts = rng.sample(list(valid), k=n_valid)
    wrong_pairs = rng.sample(list(invalid), k=n_total - n_valid)

    options: List[MCQOption] = []
    for t in correct_texts:
        options.append(MCQOption(text=str(t), is_correct=True, why_incorrect=None))
    for t, why in wrong_pairs:
        options.append(MCQOption(text=str(t), is_correct=False, why_incorrect=str(why)))

    rng.shuffle(options)

    return MCQQuiz(prompt=str(prompt), options=tuple(options))


def grade_choice(
    quiz: MCQQuiz,
    chosen: Union[int, str],
) -> Tuple[bool, str]:
    """Grade a user choice against a quiz.

    Args:
        quiz: The quiz to grade.
        chosen: Either an integer index (1-based) or a digit string.

    Returns:
        (is_correct, message). If incorrect and an explanation exists for the
        chosen decoy, the message is that explanation.
    """
    opts = list(quiz.options)

    if isinstance(chosen, int):
        idx = chosen
    else:
        s = str(chosen).strip()
        if not s.isdigit():
            return False, "Submit the choice number as an integer."
        idx = int(s)

    if idx < 1 or idx > len(opts):
        return False, f"Choice number must be between 1 and {len(opts)}."

    opt = opts[idx - 1]
    if opt.is_correct:
        return True, "Correct."

    if opt.why_incorrect:
        return False, opt.why_incorrect
    return False, "Not correct. Try again."


def render_quiz_markdown(quiz: MCQQuiz) -> str:
    """Render a quiz as simple markdown (no widgets).

    This is a fallback format for environments where ipywidgets is unavailable.
    """
    lines = [f"{i}) {o.text}" for i, o in enumerate(quiz.options, start=1)]
    return (
        quiz.prompt.strip()
        + "\n\nChoices:\n\n"
        + "\n\n".join(lines)
        + "\n\nSubmit the number of the best choice."
    )


def _try_import_widgets():
    """Best-effort import of ipywidgets + IPython display helpers.

    Returns None if the environment does not support widgets.
    """
    try:
        import ipywidgets as widgets
        from IPython.display import Markdown, HTML, display

        return widgets, display, Markdown, HTML
    except Exception:
        return None


def display_mcq_widget(
    *,
    key: str,
    valid: Sequence[str],
    invalid: Sequence[Tuple[str, str]],
    prompt: str,
    n_total: int = 5,
    n_valid: int = 1,
    seed: Optional[int] = None,
    submit_call_builder: Optional[Callable[[str, str], str]] = None,
    state: Optional[Dict[str, Any]] = None,
    state_key: Optional[str] = None,
    warn_repeat_threshold: int = 5,
    gemini_prompt_builder: Optional[Callable[[str, List[str]], str]] = None,
    show_gemini_after_wrong_attempts: int = 3,
    cooldown_after_wrong_attempts: int = 3,
    cooldown_seconds: int = 6,
) -> None:
    """Display an interactive MCQ widget in Colab (ipywidgets).

    The widget:
      - shows a prompt and a randomized set of choices
      - lets the student click **Check** to grade a selection
      - on success, reveals a copy button for the `mentor.submit_display(...)` call
      - on failure, shows an explanation (when available) and resamples choices

    Optional persisted state
    ------------------------
    If `state` is provided, interaction metadata is stored under:
        state.setdefault("mcq", {}).setdefault(state_key or key, {})

    The stored keys are:
      - wrong_attempts: count of incorrect checks
      - last_selected_text: last selected option text
      - repeat_count: number of consecutive checks on the same selected option
      - last_selected_index: 0-based index of last selected option in the UI
      - last_checked_text: last checked option text
      - last_checked_incorrect: whether the last checked option was incorrect
      - cooldown_until: unix timestamp; while now < cooldown_until, Check is disabled

    Anti-avoidance mechanisms (homework-agnostic)
    --------------------------------------------
      1) Position friction (when n_valid == 1):
         - the correct answer is not placed first on the initial render
         - after a wrong attempt, the correct answer is not placed in the same
           position the student just selected

      2) Click-spam friction:
         - re-checking the same incorrect option immediately does not re-grade

      3) Engagement support:
         - after several wrong attempts or repeated selections, a "Copy for Gemini"
           button appears. It copies a prompt (built by `gemini_prompt_builder` if
           provided, otherwise a generic prompt) without displaying that text.

      4) Cooldown:
         - after `cooldown_after_wrong_attempts` wrong checks, the Check button is
           disabled for `cooldown_seconds` seconds.

    Notes
    -----
    - This module remains homework-agnostic; step-specific content must be passed
      in via `prompt` and (optionally) `gemini_prompt_builder`.
    - The cooldown countdown uses a small background timer to refresh the widget.
      If the environment throttles UI updates, the disabling behavior still applies.
    """
    imported = _try_import_widgets()
    if imported is None:
        raise RuntimeError(
            "ipywidgets is not available in this environment. "
            "Run this in Colab or install ipywidgets."
        )

    widgets, display, Markdown, HTML = imported

    private_state: Dict[str, Any] = {}

    def _mcq_state() -> Dict[str, Any]:
        if state is None:
            return private_state
        skey = state_key if state_key is not None else key
        ns = state.setdefault("mcq", {})
        rec = ns.get(skey)
        if not isinstance(rec, dict):
            rec = {}
            ns[skey] = rec
        return rec

    st = _mcq_state()

    rng = random.Random(seed)

    def _make_quiz_constrained(*, forbidden_index: Optional[int], forbid_first_correct: bool) -> MCQQuiz:
        """Create a quiz while avoiding placing the correct option in certain positions.

        This is used to discourage random clicking when there is exactly one correct
        answer (`n_valid == 1`).

        Args:
            forbidden_index: If provided, the correct option will not be placed at
                this 0-based index.
            forbid_first_correct: If True, the correct option will not be placed
                at index 0.
        """
        q = make_quiz(
            prompt=prompt,
            valid=valid,
            invalid=invalid,
            n_total=n_total,
            n_valid=n_valid,
            seed=rng.randrange(2**32),
        )

        if n_valid != 1:
            return q

        opts = list(q.options)
        correct_opt = next((o for o in opts if o.is_correct), None)
        if correct_opt is None:
            return q

        decoys = [o for o in opts if not o.is_correct]
        rng.shuffle(decoys)

        bans = set()
        if forbid_first_correct:
            bans.add(0)
        if forbidden_index is not None:
            bans.add(int(forbidden_index))

        positions = [i for i in range(len(opts)) if i not in bans]
        if not positions:
            positions = list(range(len(opts)))

        correct_pos = rng.choice(positions)

        new_opts: List[MCQOption] = []
        di = 0
        for i in range(len(opts)):
            if i == correct_pos:
                new_opts.append(correct_opt)
            else:
                new_opts.append(decoys[di])
                di += 1

        return MCQQuiz(prompt=q.prompt, options=tuple(new_opts))

    quiz = _make_quiz_constrained(forbidden_index=None, forbid_first_correct=True)

    why_map = quiz.why_map()
    correct_texts = set(quiz.correct_texts())
    if not correct_texts:
        raise RuntimeError("No correct option present")

    # Persisted interaction state (only meaningful if the caller passes a shared `state` dict).
    # These fields are used to add friction against repeated random clicking without
    # embedding any step-specific content.
    st.setdefault("wrong_attempts", 0)
    st.setdefault("last_selected_text", None)
    st.setdefault("repeat_count", 0)
    st.setdefault("last_selected_index", None)
    st.setdefault("last_checked_text", None)
    st.setdefault("last_checked_incorrect", False)
    st.setdefault("cooldown_until", 0.0)

    if submit_call_builder is None:
        def submit_call_builder(k: str, v: str) -> str:
            return f'mentor.submit_display("{k}", {v!r})'

    radio = widgets.RadioButtons(
        options=[o.text for o in quiz.options],
        description="",
        layout=widgets.Layout(width="100%"),
    )
    btn = widgets.Button(description="Check")
    out = widgets.Output()

    cooldown_msg = widgets.HTML(value="")
    _cooldown_timer: Dict[str, Any] = {"t": None}

    def _cooldown_remaining() -> float:
        try:
            until = float(st.get("cooldown_until", 0.0) or 0.0)
        except Exception:
            until = 0.0
        return max(0.0, until - time.time())

    def _set_cooldown(seconds: int) -> None:
        st["cooldown_until"] = float(time.time() + max(0, int(seconds)))

    def _apply_cooldown_ui() -> None:
        if _cooldown_timer.get("t") is not None:
            try:
                _cooldown_timer["t"].cancel()
            except Exception:
                pass
            _cooldown_timer["t"] = None

        def tick() -> None:
            rem = _cooldown_remaining()
            if rem <= 0.0:
                btn.disabled = False
                cooldown_msg.value = ""
                _cooldown_timer["t"] = None
                return
            btn.disabled = True
            cooldown_msg.value = f"<div style='color:#6a737d; font-size:13px;'>Cooldown: wait {int(rem + 0.999)}s, then try again.</div>"
            t = threading.Timer(1.0, tick)
            t.daemon = True
            _cooldown_timer["t"] = t
            t.start()

        tick()

    if _cooldown_remaining() > 0.0:
        _apply_cooldown_ui()

    def _resample_quiz(*, forbidden_index: Optional[int], forbid_first_correct: bool) -> None:
        nonlocal quiz, why_map, correct_texts
        quiz = _make_quiz_constrained(
            forbidden_index=forbidden_index,
            forbid_first_correct=forbid_first_correct,
        )
        why_map = quiz.why_map()
        correct_texts = set(quiz.correct_texts())
        if not correct_texts:
            raise RuntimeError("No correct option present")
        new_opts = [o.text for o in quiz.options]
        radio.options = new_opts
        radio.value = new_opts[0] if new_opts else None

    def _default_gemini_prompt(prompt_str: str, options_list: List[str]) -> str:
        lines: List[str] = []
        lines.append(prompt_str.strip())
        lines.append("")
        lines.append("Choices:")
        for i, opt in enumerate(options_list, 1):
            lines.append(f"{i}) {opt}")
        lines.append("")
        lines.append("Pick the best choice. Return the exact option text only.")
        return "\n".join(lines)

    def _copy_block(code: str) -> Any:
        suffix = uuid.uuid4().hex[:10]
        btn_id = f"mcq_copy_btn_{suffix}"
        msg_id = f"mcq_copy_msg_{suffix}"
        pre_id = f"mcq_copy_pre_{suffix}"
        code_html = html.escape(code)
        return HTML(
            "<div style='display:flex; align-items:center; gap:10px; margin:8px 0 6px 0;'>"
            "<div style='font-weight:700;'>Run:</div>"
            f"<button id='{btn_id}' style='padding:6px 10px; border:1px solid #ccc; border-radius:6px; background:#fff; cursor:pointer;'>Copy</button>"
            f"<span id='{msg_id}' style='font-size:13px; color:#555;'></span>"
            "</div>"
            f"<pre id='{pre_id}' style='margin:0; padding:10px; background:#f6f8fa; border:1px solid #ddd; border-radius:8px; overflow:auto; border-radius:8px;'><code>{code_html}</code></pre>"
            "<script>(function(){"
            f"var btn=document.getElementById('{btn_id}');"
            f"var msg=document.getElementById('{msg_id}');"
            f"var code=document.getElementById('{pre_id}').innerText;"
            "function done(ok){msg.textContent=ok?'Copied.':'Copy failed.'; setTimeout(function(){msg.textContent='';},1200);}"
            "btn.onclick=function(){"
            "if(navigator && navigator.clipboard && navigator.clipboard.writeText){"
            "navigator.clipboard.writeText(code).then(function(){done(true);}).catch(function(){done(false);});"
            "}else{"
            "try{var ta=document.createElement('textarea'); ta.value=code; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); done(true);}catch(e){done(false);}"
            "}" 
            "};"
            "})();</script>"
        )

    def _copy_button(label: str, text: str) -> Any:
        suffix = uuid.uuid4().hex[:10]
        btn_id = f"mcq_copyonly_btn_{suffix}"
        msg_id = f"mcq_copyonly_msg_{suffix}"

        safe = text.replace("\\", "\\\\").replace("'", "\\'")
        safe = safe.replace("\r\n", "\n").replace("\r", "\n")
        safe = safe.replace("</", "<\\/")

        return HTML(
            "<div style='display:flex; align-items:center; gap:10px; margin:8px 0 0 0;'>"
            f"<button id='{btn_id}' style='padding:6px 10px; border:1px solid #ccc; border-radius:6px; background:#fff; cursor:pointer;'>{html.escape(label)}</button>"
            f"<span id='{msg_id}' style='font-size:13px; color:#555;'></span>"
            "</div>"
            "<script>(function(){"
            f"var btn=document.getElementById('{btn_id}');"
            f"var msg=document.getElementById('{msg_id}');"
            f"var text='{safe}';"
            "function done(ok){msg.textContent=ok?'Copied.':'Copy failed.'; setTimeout(function(){msg.textContent='';},1200);}"
            "btn.onclick=function(){"
            "if(navigator && navigator.clipboard && navigator.clipboard.writeText){"
            "navigator.clipboard.writeText(text).then(function(){done(true);}).catch(function(){done(false);});"
            "}else{"
            "try{var ta=document.createElement('textarea'); ta.value=text; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); done(true);}catch(e){done(false);}"
            "}"
            "};"
            "})();</script>"
        )

    def _maybe_show_gemini_button() -> None:
        wa = int(st.get("wrong_attempts", 0) or 0)
        rc = int(st.get("repeat_count", 0) or 0)
        if (wa >= int(show_gemini_after_wrong_attempts)) or (rc >= int(warn_repeat_threshold)):
            options_texts = list(radio.options)
            if gemini_prompt_builder is not None:
                gemini_text = gemini_prompt_builder(prompt, options_texts)
            else:
                gemini_text = _default_gemini_prompt(prompt, options_texts)
            display(_copy_button("Copy for Gemini", gemini_text))

    def on_click(_):
        out.clear_output()
        with out:
            chosen_text = radio.value

            rem0 = _cooldown_remaining()
            if rem0 > 0.0:
                cooldown_msg.value = f"<div style='color:#6a737d; font-size:13px;'>Cooldown: wait {int(rem0 + 0.999)}s, then try again.</div>"
                btn.disabled = True
                return

            options_list = list(radio.options)
            try:
                chosen_index = options_list.index(chosen_text) if chosen_text is not None else None
            except ValueError:
                chosen_index = None

            st["last_selected_index"] = chosen_index

            last_text = st.get("last_selected_text")
            if chosen_text is not None and chosen_text == last_text:
                st["repeat_count"] = int(st.get("repeat_count", 0)) + 1
            else:
                st["repeat_count"] = 1 if chosen_text is not None else 0
            st["last_selected_text"] = chosen_text

            if int(st.get("repeat_count", 0)) >= int(warn_repeat_threshold):
                display(Markdown("⚠️ You have selected the same option repeatedly. Please choose thoughtfully."))
                _maybe_show_gemini_button()

            last_checked_text = st.get("last_checked_text")
            last_checked_incorrect = bool(st.get("last_checked_incorrect"))
            if last_checked_incorrect and chosen_text is not None and chosen_text == last_checked_text:
                display(Markdown("⚠️ You already checked this option and it was incorrect. Pick a different option before checking again."))
                _maybe_show_gemini_button()
                return

            if chosen_text in correct_texts:
                st["last_checked_text"] = chosen_text
                st["last_checked_incorrect"] = False
                display(Markdown("**Correct.** Use the button to copy the line below into a new code cell:"))
                call = submit_call_builder(key, chosen_text)
                display(_copy_block(call))
            else:
                st["last_checked_text"] = chosen_text
                st["last_checked_incorrect"] = True
                st["wrong_attempts"] = int(st.get("wrong_attempts", 0)) + 1
                if int(st.get("wrong_attempts", 0)) >= int(cooldown_after_wrong_attempts):
                    _set_cooldown(int(cooldown_seconds))
                why = why_map.get(chosen_text, "Not quite.")
                display(Markdown("**Not quite.** " + why))
                display(Markdown("Generating a new set of choices. Try again."))
                _resample_quiz(
                    forbidden_index=st.get("last_selected_index"),
                    forbid_first_correct=False,
                )
                _maybe_show_gemini_button()
                if _cooldown_remaining() > 0.0:
                    _apply_cooldown_ui()

    btn.on_click(on_click)

    display(Markdown(prompt.strip()))
    display(radio, btn, cooldown_msg, out)
