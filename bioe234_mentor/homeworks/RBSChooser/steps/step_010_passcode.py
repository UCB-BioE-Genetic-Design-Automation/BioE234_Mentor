from pathlib import Path
import hashlib

_ALLOWED_SHA1: set[str] | None = None
_ALLOWED_SHA1_PATH: Path | None = None


def _load_allowed_sha1() -> set[str]:
    global _ALLOWED_SHA1
    global _ALLOWED_SHA1_PATH
    if _ALLOWED_SHA1 is not None:
        return _ALLOWED_SHA1

    candidates = [
        Path(__file__).resolve().parent.parent / "fixtures" / "sha1_whitelist.csv",
        # Path(__file__).resolve().parents[4] / "sha1_whitelist.csv",
    ]

    path: Path | None = None
    for p in candidates:
        if p.exists() and p.is_file():
            path = p
            break

    _ALLOWED_SHA1_PATH = path

    if path is None:
        _ALLOWED_SHA1_PATH = None
        _ALLOWED_SHA1 = set()
        return _ALLOWED_SHA1

    allowed: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        s = s.lstrip("\ufeff")
        if s.lower() == "sha1":
            continue
        if "," in s:
            s = s.split(",", 1)[0].strip()
        s = s.strip().lower()
        if len(s) != 40:
            continue
        if any(c not in "0123456789abcdef" for c in s):
            continue
        allowed.add(s)

    _ALLOWED_SHA1 = allowed
    return _ALLOWED_SHA1


def debug_info() -> dict:
    allowed = _load_allowed_sha1()
    return {
        "allowed_count": len(allowed),
        "allowed_path": str(_ALLOWED_SHA1_PATH) if _ALLOWED_SHA1_PATH is not None else None,
    }


STEP_ID = "010"
KEY = "PASSCODE"
TITLE = "Passcode entry"
NEXT_STEP = "020"
HASH_MODE = "json"
SUBMIT_STUB = 'mentor.submit("PASSCODE", "<your_passcode>")'


def render(state) -> str:
    return (
        "Paste your passcode as a single word containing letters only.\n\n"
        "If you include spaces, numbers, or punctuation, resubmit with only the passcode.\n"
    )


def shape_check(answer):
    if not isinstance(answer, str):
        return False, "Expected a string."
    s = answer.strip()
    if not s:
        return False, "Passcode was empty."
    if not s.isalpha():
        return False, "Passcode must contain letters only (no spaces, numbers, or punctuation)."
    if " " in s:
        return False, "Passcode must be a single word (no spaces)."
    return True, "ok"


def validate(answer, state):
    s = str(answer).strip()

    allowed = _load_allowed_sha1()
    if not allowed:
        return False, "Passcode validation data file not found.", {"passcode_len": len(s)}

    candidates = [
        (s, "as_entered"),
        (s.lower(), "lower"),
    ]

    for cand, mode in candidates:
        h = hashlib.sha1(cand.encode("utf-8")).hexdigest()
        if h in allowed:
            return True, "Passcode recorded.", {
                "passcode_len": len(s),
                "passcode_sha1": h,
                "passcode_sha1_mode": mode,
            }

    return False, "Passcode not recognized. Double-check and resubmit.", {"passcode_len": len(s)}
