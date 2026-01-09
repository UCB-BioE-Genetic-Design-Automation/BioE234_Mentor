from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import json
import runpy

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
            snippet = step.submit_stub
        else:
            snippet = f'mentor.submit("{step.key}", <your_answer_here>)'

        return f"## {step.title}\n\n{body}\n\n**Submit:**\n```python\n{snippet}\n```"

    def submit(self, key: str, answer: Any) -> str:
        if self.is_finished():
            return self.final_report()

        step = self._load_step(self.current_step_id())

        if key != step.key:
            snippet = step.submit_stub or f'mentor.submit("{step.key}", <your_answer_here>)'
            return (
                "## Not quite\n\n"
                f"You are currently on step **{step.step_id}** and I am expecting key **{step.key}**.\n\n"
                "**Try:**\n"
                f"```python\n{snippet}\n```"
            )

        ok, reason = step.shape_check(answer)
        if not ok:
            snippet = step.submit_stub or f'mentor.submit("{step.key}", <your_answer_here>)'
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
                snippet = step.submit_stub or f'mentor.submit("{step.key}", <your_answer_here>)'
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
            snippet = step.submit_stub or f'mentor.submit("{step.key}", <your_answer_here>)'
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
