from __future__ import annotations

from typing import Any, Callable, Dict, List, Tuple
import inspect
import re

CheckFn = Callable[[Any, Dict[str, Any]], Tuple[bool, str]]


def nonempty_string(x: Any, state: Dict[str, Any]) -> Tuple[bool, str]:
    if not isinstance(x, str):
        return False, "Expected a string."
    if not x.strip():
        return False, "String was empty."
    return True, "ok"


def regex_fullmatch(pattern: str, message: str) -> CheckFn:
    rx = re.compile(pattern)

    def _check(x: Any, state: Dict[str, Any]) -> Tuple[bool, str]:
        if not isinstance(x, str):
            return False, "Expected a string."
        if rx.fullmatch(x.strip()) is None:
            return False, message
        return True, "ok"

    return _check


def dict_has_keys(required: List[str]) -> CheckFn:
    req = list(required)

    def _check(x: Any, state: Dict[str, Any]) -> Tuple[bool, str]:
        if not isinstance(x, dict):
            return False, f"Expected a dict with keys {req}."
        missing = [k for k in req if k not in x]
        if missing:
            return False, f"Missing required keys: {missing}"
        return True, "ok"

    return _check


def list_min_len(n: int) -> CheckFn:
    def _check(x: Any, state: Dict[str, Any]) -> Tuple[bool, str]:
        if not isinstance(x, list):
            return False, f"Expected a list of length at least {n}."
        if len(x) < n:
            return False, f"List length was {len(x)}, expected at least {n}."
        return True, "ok"

    return _check


def is_callable(x: Any, state: Dict[str, Any]) -> Tuple[bool, str]:
    if not callable(x):
        return False, "Expected a callable."
    return True, "ok"


def callable_min_positional_args(n: int) -> CheckFn:
    def _check(x: Any, state: Dict[str, Any]) -> Tuple[bool, str]:
        if not callable(x):
            return False, "Expected a callable."
        try:
            sig = inspect.signature(x)
            params = [
                p
                for p in sig.parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            ]
            if len(params) < n:
                return False, f"Callable must accept at least {n} positional argument(s)."
        except Exception:
            return True, "ok"
        return True, "ok"

    return _check
