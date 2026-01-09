from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union
import random


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
    lines = [f"{i}) {o.text}" for i, o in enumerate(quiz.options, start=1)]
    return (
        quiz.prompt.strip()
        + "\n\nChoices:\n\n"
        + "\n\n".join(lines)
        + "\n\nSubmit the number of the best choice."
    )


def _try_import_widgets():
    try:
        import ipywidgets as widgets
        from IPython.display import Markdown, display

        return widgets, display, Markdown
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
) -> None:
    imported = _try_import_widgets()
    if imported is None:
        raise RuntimeError(
            "ipywidgets is not available in this environment. "
            "Run this in Colab or install ipywidgets."
        )

    widgets, display, Markdown = imported

    rng = random.Random(seed)

    quiz = make_quiz(
        prompt=prompt,
        valid=valid,
        invalid=invalid,
        n_total=n_total,
        n_valid=n_valid,
        seed=rng.randrange(2**32),
    )

    why_map = quiz.why_map()
    correct_texts = set(quiz.correct_texts())
    if not correct_texts:
        raise RuntimeError("No correct option present")

    def _resample_quiz() -> None:
        nonlocal quiz, why_map, correct_texts
        quiz = make_quiz(
            prompt=prompt,
            valid=valid,
            invalid=invalid,
            n_total=n_total,
            n_valid=n_valid,
            seed=rng.randrange(2**32),
        )
        why_map = quiz.why_map()
        correct_texts = set(quiz.correct_texts())
        if not correct_texts:
            raise RuntimeError("No correct option present")
        new_opts = [o.text for o in quiz.options]
        radio.options = new_opts
        radio.value = new_opts[0] if new_opts else None

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

    def on_click(_):
        out.clear_output()
        with out:
            chosen_text = radio.value
            if chosen_text in correct_texts:
                display(Markdown("**Correct.** Copy and paste this into a new code cell:"))
                call = submit_call_builder(key, chosen_text)
                display(Markdown("```python\n" + call + "\n```"))
            else:
                why = why_map.get(chosen_text, "Not quite.")
                display(Markdown("**Not quite.** " + why))
                display(Markdown("Generating a new set of choices. Try again."))
                _resample_quiz()

    btn.on_click(on_click)

    display(Markdown(prompt.strip()))
    display(radio, btn, out)
