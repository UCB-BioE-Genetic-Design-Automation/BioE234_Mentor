from __future__ import annotations

from pathlib import Path
import argparse
import ast
import json

from bioe234_mentor.mentor import Mentor


def _parse_answer(raw: str, mode: str):
    s = raw.strip()
    if mode == "file":
        return s
    if mode == "callable":
        try:
            return eval(s, {})
        except Exception:
            return s
    if not s:
        return ""
    if s.startswith("{") or s.startswith("["):
        try:
            return json.loads(s)
        except Exception:
            pass
    try:
        return ast.literal_eval(s)
    except Exception:
        return s


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--homework", default="RBSChooser")
    p.add_argument("--start_step", default="010")
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--passcode", default=None)
    args = p.parse_args()

    state_dir = Path(".mentor_state")
    state_path = state_dir / f"{args.homework}.json"

    if args.fresh and state_path.exists():
        state_path.unlink()

    mentor = Mentor.load_or_create(homework=args.homework, state_dir=state_dir)
    mentor._state["current_step_id"] = str(args.start_step).zfill(3)

    if args.passcode is not None:
        mentor._state["passcode"] = str(args.passcode).strip()

    mentor._save()

    while True:
        if mentor.is_finished():
            print(mentor.final_report())
            return

        print(mentor.show())

        step = mentor._load_step(mentor.current_step_id())
        prompt = f"Enter value for {step.key} (or :quit, :status): "
        raw = input(prompt)

        if raw.strip() == ":quit":
            return
        if raw.strip() == ":status":
            print(mentor.status())
            continue

        answer = _parse_answer(raw, step.hash_mode)
        out = mentor.submit(step.key, answer)
        print(out)


if __name__ == "__main__":
    main()