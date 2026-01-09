from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple
import hashlib
import inspect
import json
import time


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def stable_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha1_hex_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def sha1_hex_bytes(data: bytes) -> str:
    return hashlib.sha1(data).hexdigest()


def sha1_hex_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fingerprint_callable(fn: Any) -> Tuple[str, Dict[str, Any]]:
    meta: Dict[str, Any] = {}
    try:
        src = inspect.getsource(fn)
        meta["fingerprint_mode"] = "source"
        meta["callable_name"] = getattr(fn, "__name__", None)
        meta["callable_qualname"] = getattr(fn, "__qualname__", None)
        return sha1_hex_text(src), meta
    except Exception:
        code = getattr(fn, "__code__", None)
        if code is None:
            meta["fingerprint_mode"] = "repr"
            return sha1_hex_text(repr(fn)), meta
        payload = (
            code.co_code
            + repr(code.co_consts).encode("utf-8")
            + repr(code.co_names).encode("utf-8")
        )
        meta["fingerprint_mode"] = "bytecode"
        meta["callable_name"] = getattr(fn, "__name__", None)
        meta["callable_qualname"] = getattr(fn, "__qualname__", None)
        meta["argcount"] = getattr(code, "co_argcount", None)
        return sha1_hex_bytes(payload), meta


def fingerprint_submission(answer: Any, mode: str) -> Tuple[str, Dict[str, Any]]:
    meta: Dict[str, Any] = {"hash_mode": mode}

    if mode == "file":
        p = Path(str(answer)).expanduser()
        if not p.exists() or not p.is_file():
            raise FileNotFoundError(str(p))
        meta["file"] = str(p)
        meta["bytes"] = p.stat().st_size
        return sha1_hex_file(p), meta

    if mode == "callable":
        h, cmeta = fingerprint_callable(answer)
        meta.update(cmeta)
        return h, meta

    s = stable_json(answer)
    meta["json_len"] = len(s)
    return sha1_hex_text(s), meta
