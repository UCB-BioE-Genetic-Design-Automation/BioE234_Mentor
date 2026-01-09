from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import json
import runpy
import html
import uuid

from . import loaders
from .util import now_iso, fingerprint_submission, stable_json


@dataclass(frozen=True)
class LoadedStep:
    step_id: str
    key: str
    title: str
    next_step: Optional[str]
    render: Any
    shape_check: Any
    validate: Optional[Any]
    hash_mode: str
    submit_stub: Optional[str]


class Mentor:
    _display_seq = 0

    def __init__(
        self,
        homework: str,
        state_dir: Path = Path(".mentor_state"),
        base_dir: Optional[Path] = None,
    ):
        self.homework = homework
        self.base_dir = base_dir
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.step_map = loaders.discover_steps(homework)
        self.step_ids = loaders.ordered_step_ids(self.step_map)
        if not self.step_ids:
            raise RuntimeError("No steps found.")
        self.state_path = self.state_dir / f"{homework}.json"
        self._state: Dict[str, Any] = {
            "homework": homework,
            "created_at": now_iso(),
            "current_step_id": self.step_ids[0],
            "passcode": None,
            "submissions": {},
            "history": [],
        }

    @classmethod
    def load_or_create(
        cls,
        homework: str,
        state_dir: Path = Path(".mentor_state"),
        base_dir: Optional[Path] = None,
    ) -> "Mentor":
        m = cls(homework=homework, state_dir=state_dir, base_dir=base_dir)
        if m.state_path.exists():
            m._state = json.loads(m.state_path.read_text(encoding="utf-8"))
        return m

    def _save(self) -> None:
        self.state_path.write_text(
            json.dumps(self._state, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _log(self, event: str, details: Dict[str, Any]) -> None:
        self._state["history"].append({"ts": now_iso(), "event": event, "details": details})

    def is_finished(self) -> bool:
        return self._state.get("current_step_id") == "DONE"

    def current_step_id(self) -> str:
        return str(self._state.get("current_step_id"))

    def _load_step(self, step_id: str) -> LoadedStep:
        ref = self.step_map.get(step_id)
        if ref is None:
            raise RuntimeError(f"Unknown step_id: {step_id}")
        ns = runpy.run_path(str(ref.path))

        step_id_val = ns.get("STEP_ID")
        key = ns.get("KEY")
        title = ns.get("TITLE")
        render = ns.get("render")
        shape_check = ns.get("shape_check")

        if str(step_id_val) != str(step_id):
            raise RuntimeError(f"Step file STEP_ID mismatch for {ref.path.name}")
        if not isinstance(key, str) or not key.strip():
            raise RuntimeError(f"Missing or invalid KEY in {ref.path.name}")
        if not isinstance(title, str) or not title.strip():
            raise RuntimeError(f"Missing or invalid TITLE in {ref.path.name}")
        if not callable(render):
            raise RuntimeError(f"Missing render(state) in {ref.path.name}")
        if not callable(shape_check):
            raise RuntimeError(f"Missing shape_check(answer) in {ref.path.name}")

        next_step = ns.get("NEXT_STEP")
        if next_step is not None:
            next_step = str(next_step)

        validate = ns.get("validate")
        if validate is not None and not callable(validate):
            raise RuntimeError(f"validate must be callable if present in {ref.path.name}")

        hash_mode = ns.get("HASH_MODE", "json")
        if not isinstance(hash_mode, str):
            hash_mode = "json"

        submit_stub = ns.get("SUBMIT_STUB")
        if submit_stub is not None and not isinstance(submit_stub, str):
            submit_stub = None

        return LoadedStep(
            step_id=step_id,
            key=key,
            title=title,
            next_step=next_step,
            render=render,
            shape_check=shape_check,
            validate=validate,
            hash_mode=hash_mode,
            submit_stub=submit_stub,
        )

    def show(self) -> str:
        if self.is_finished():
            return self.final_report()

        step = self._load_step(self.current_step_id())
        body = str(step.render(self._state)).strip()

        if step.submit_stub:
            raw_snippet = step.submit_stub
        else:
            raw_snippet = f'mentor.submit_display("{step.key}", <your_answer_here>)'

        snippet = raw_snippet
        if raw_snippet.lstrip().startswith("mentor.submit("):
            snippet = raw_snippet.replace("mentor.submit(", "mentor.submit_display(", 1)

        return f"## {step.title}\n\n{body}\n\n**Submit:**\n```python\n{snippet}\n```"

    def show_md(self):
        try:
            from IPython.display import Markdown
        except Exception:
            return self.show()
        return Markdown(self.show())

    def _repr_markdown_(self) -> str:
        return self.show()

    def _html_block(self) -> str:
        if self.is_finished():
            return f"<pre>{html.escape(self.final_report())}</pre>"

        step = self._load_step(self.current_step_id())
        body = str(step.render(self._state)).strip()
        raw_snippet = step.submit_stub or f'mentor.submit_display("{step.key}", <your_answer_here>)'
        snippet = raw_snippet
        if raw_snippet.lstrip().startswith("mentor.submit("):
            snippet = raw_snippet.replace("mentor.submit(", "mentor.submit_display(", 1)

        self.__class__._display_seq += 1
        suffix = f"{self.__class__._display_seq}_{uuid.uuid4().hex[:8]}"
        btn_id = f"mentor_copy_btn_{suffix}"
        msg_id = f"mentor_copy_msg_{suffix}"
        code_id = f"mentor_code_{suffix}"

        title = html.escape(step.title)
        body_html = html.escape(body).replace("\n", "<br>")
        code_html = html.escape(snippet)

        block = (
            "<div style='font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; line-height:1.4;'>"
            "<div style='font-size:22px; font-weight:700; margin:0 0 10px 0; line-height:1.2;'>" + title + "</div>"
            "<div style='font-size:15px; margin:0 0 14px 0;'>" + body_html + "</div>"
            "<div style='display:flex; align-items:center; gap:10px; margin:0 0 6px 0;'>"
            "<div style='font-weight:700;'>Run:</div>"
            f"<button id='{btn_id}' style='padding:6px 10px; border:1px solid #ccc; border-radius:6px; background:#fff; cursor:pointer;'>Copy</button>"
            f"<span id='{msg_id}' style='font-size:13px; color:#555;'></span>"
            "</div>"
            f"<pre id='{code_id}' style='margin:0; padding:10px; background:#f6f8fa; border:1px solid #ddd; border-radius:8px; overflow:auto;'>"
            "<code>" + code_html + "</code></pre>"
            "<script>"
            "(function(){"
            f"var btn=document.getElementById('{btn_id}');"
            f"var msg=document.getElementById('{msg_id}');"
            f"var code=document.getElementById('{code_id}').innerText;"
            "function done(ok){msg.textContent=ok?'Copied.':'Copy failed.'; setTimeout(function(){msg.textContent='';},1200);}"
            "btn.onclick=function(){"
            "if(navigator && navigator.clipboard && navigator.clipboard.writeText){"
            "navigator.clipboard.writeText(code).then(function(){done(true);}).catch(function(){done(false);});"
            "}else{"
            "try{var ta=document.createElement('textarea'); ta.value=code; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); done(true);}catch(e){done(false);}"
            "}"
            "};"
            "})();"
            "</script>"
            "</div>"
        )

        return block

    def show_html(self):
        try:
            from IPython.display import HTML
        except Exception:
            return self.show()
        return HTML(self._html_block())

    def _repr_html_(self) -> str:
        return self._html_block()

    def display(self) -> None:
        try:
            from IPython.display import display
        except Exception:
            print(self.show())
            return
        display(self.show_html())

    def submit_display(self, key: str, answer: Any) -> None:
        prev_step = self.current_step_id()
        out = self.submit(key, answer)

        advanced = (self.current_step_id() != prev_step) or self.is_finished()

        if advanced:
            self.display()
            return

        try:
            from IPython.display import display, Markdown
        except Exception:
            print(out)
            return

        display(Markdown(out))

    def submit(self, key: str, answer: Any) -> str:
        if self.is_finished():
            return self.final_report()

        step = self._load_step(self.current_step_id())

        if key != step.key:
            raw_snippet = step.submit_stub or f'mentor.submit_display("{step.key}", <your_answer_here>)'
            snippet = raw_snippet
            if raw_snippet.lstrip().startswith("mentor.submit("):
                snippet = raw_snippet.replace("mentor.submit(", "mentor.submit_display(", 1)
            return (
                "## Not quite\n\n"
                f"You are currently on step **{step.step_id}** and I am expecting key **{step.key}**.\n\n"
                "**Try:**\n"
                f"```python\n{snippet}\n```"
            )

        ok, reason = step.shape_check(answer)
        if not ok:
            raw_snippet = step.submit_stub or f'mentor.submit_display("{step.key}", <your_answer_here>)'
            snippet = raw_snippet
            if raw_snippet.lstrip().startswith("mentor.submit("):
                snippet = raw_snippet.replace("mentor.submit(", "mentor.submit_display(", 1)
            return (
                "## Try again\n\n"
                f"Your submission for **{step.key}** did not match the expected shape.\n\n"
                f"**Issue:** {reason}\n\n"
                "**Resubmit:**\n"
                f"```python\n{snippet}\n```"
            )

        summary: Dict[str, Any] = {}
        student_note = ""
        if step.validate is not None:
            v_ok, v_msg, v_summary = step.validate(answer, self._state)
            if not v_ok:
                raw_snippet = step.submit_stub or f'mentor.submit_display("{step.key}", <your_answer_here>)'
                snippet = raw_snippet
                if raw_snippet.lstrip().startswith("mentor.submit("):
                    snippet = raw_snippet.replace("mentor.submit(", "mentor.submit_display(", 1)
                return (
                    "## Try again\n\n"
                    f"I ran a check for **{step.key}** and it did not pass.\n\n"
                    f"**Issue:** {v_msg}\n\n"
                    "**Resubmit:**\n"
                    f"```python\n{snippet}\n```"
                )
            student_note = str(v_msg or "")
            if isinstance(v_summary, dict):
                summary = v_summary
            else:
                summary = {"summary": v_summary}

        try:
            sha1, meta = fingerprint_submission(answer, step.hash_mode)
        except FileNotFoundError as e:
            raw_snippet = step.submit_stub or f'mentor.submit_display("{step.key}", <your_answer_here>)'
            snippet = raw_snippet
            if raw_snippet.lstrip().startswith("mentor.submit("):
                snippet = raw_snippet.replace("mentor.submit(", "mentor.submit_display(", 1)
            return (
                "## Try again\n\n"
                f"I expected a file path for **{step.key}**, but this file does not exist:\n\n"
                f"`{e.args[0]}`\n\n"
                "**Resubmit:**\n"
                f"```python\n{snippet}\n```"
            )

        stored_value: Any
        if step.hash_mode == "file":
            stored_value = str(Path(str(answer)).expanduser())
        elif step.hash_mode == "callable":
            stored_value = {
                "callable_name": meta.get("callable_name"),
                "callable_qualname": meta.get("callable_qualname"),
                "fingerprint_mode": meta.get("fingerprint_mode"),
            }
        else:
            try:
                stable_json(answer)
                stored_value = answer
            except TypeError:
                stored_value = {"repr": repr(answer)}

        try:
            stable_json(summary)
        except TypeError:
            summary = {"repr": repr(summary)}

        self._state["submissions"][step.key] = {
            "step_id": step.step_id,
            "key": step.key,
            "submitted_at": now_iso(),
            "sha1": sha1,
            "meta": meta,
            "value": stored_value,
            "summary": summary,
        }

        if step.key == "PASSCODE":
            self._state["passcode"] = str(answer).strip()

        self._log("submit", {"step_id": step.step_id, "key": step.key, "sha1": sha1})
        self._advance(step)
        self._save()

        if student_note:
            return f"## Recorded\n\n{student_note.strip()}\n\n" + self.show()

        return self.show()

    def _advance(self, step: LoadedStep) -> None:
        nxt = step.next_step
        if nxt is None:
            idx = self.step_ids.index(step.step_id)
            if idx == len(self.step_ids) - 1:
                self._state["current_step_id"] = "DONE"
                return
            self._state["current_step_id"] = self.step_ids[idx + 1]
            return

        if nxt.upper() == "DONE":
            self._state["current_step_id"] = "DONE"
            return

        if nxt not in self.step_map:
            raise RuntimeError(f"NEXT_STEP points to missing step_id: {nxt}")

        self._state["current_step_id"] = nxt

    def status(self) -> Dict[str, Any]:
        return {
            "homework": self.homework,
            "current_step_id": self.current_step_id(),
            "is_finished": self.is_finished(),
            "submitted_keys": sorted(list(self._state.get("submissions", {}).keys())),
        }

    def final_report(self) -> str:
        subs = self._state.get("submissions", {})
        passcode = self._state.get("passcode")
        lines: list[str] = []
        lines.append("## Final submission package\n")
        lines.append("Copy and paste the block below into bCourses.\n")
        lines.append("```text")
        lines.append(f"HOMEWORK: {self.homework}")
        lines.append(f"PASSCODE: {passcode}")
        lines.append(f"CREATED_AT: {self._state.get('created_at')}")
        lines.append(f"STATE_SAVED_AT: {now_iso()}")
        lines.append("")
        lines.append("SUBMISSIONS:")
        for k in sorted(subs.keys()):
            rec = subs[k]
            lines.append(f"- {k}")
            lines.append(f"  step_id: {rec.get('step_id')}")
            lines.append(f"  submitted_at: {rec.get('submitted_at')}")
            lines.append(f"  sha1: {rec.get('sha1')}")
            meta = rec.get("meta", {})
            for mk in sorted(meta.keys()):
                lines.append(f"  {mk}: {meta[mk]}")
            summary = rec.get("summary", {})
            if summary:
                try:
                    s = stable_json(summary)
                except TypeError:
                    s = json.dumps({"repr": repr(summary)}, ensure_ascii=False)
                lines.append(f"  summary_sha1: {fingerprint_submission(s, 'json')[0]}")
        lines.append("```")
        return "\n".join(lines)
