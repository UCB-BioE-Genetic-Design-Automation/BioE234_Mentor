from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
import importlib
import re


@dataclass(frozen=True)
class StepRef:
    step_id: str
    path: Path


def package_root() -> Path:
    return Path(__file__).resolve().parent


def homeworks_root() -> Path:
    return package_root() / "homeworks"


def list_homeworks() -> List[str]:
    root = homeworks_root()
    if not root.exists():
        return []
    out: List[str] = []
    for p in sorted(root.iterdir()):
        if p.is_dir() and (p / "homework.py").exists():
            out.append(p.name)
    return out


def steps_dir(homework: str) -> Path:
    mod = importlib.import_module(f"bioe234_mentor.homeworks.{homework}.homework")
    fn = getattr(mod, "steps_dir", None)
    if fn is not None and callable(fn):
        d = fn()
        return Path(d)
    return package_root() / "homeworks" / homework / "steps"


def discover_steps(homework: str) -> Dict[str, StepRef]:
    d = steps_dir(homework)
    if not d.exists():
        raise FileNotFoundError(str(d))

    rx = re.compile(r"^step_(\d{3})_.*\.py$")
    refs: List[StepRef] = []
    for p in sorted(d.glob("step_*.py")):
        m = rx.match(p.name)
        if m is None:
            continue
        sid = m.group(1)
        refs.append(StepRef(step_id=sid, path=p))

    if not refs:
        raise RuntimeError(f"No step files found in {d}")

    out: Dict[str, StepRef] = {}
    for r in refs:
        if r.step_id in out:
            raise RuntimeError(f"Duplicate step_id detected: {r.step_id}")
        out[r.step_id] = r

    return out


def ordered_step_ids(step_map: Dict[str, StepRef]) -> List[str]:
    return sorted(step_map.keys())
