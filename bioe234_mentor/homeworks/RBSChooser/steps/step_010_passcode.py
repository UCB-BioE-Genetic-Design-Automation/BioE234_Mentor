from pathlib import Path
import hashlib
import importlib.resources as ir

_ALLOWED_SHA1: set[str] | None = None
_ALLOWED_SHA1_PATH: Path | None = None


def _load_allowed_sha1() -> set[str]:
    global _ALLOWED_SHA1
    global _ALLOWED_SHA1_PATH
    if _ALLOWED_SHA1 is not None:
        return _ALLOWED_SHA1

    text: str | None = None

    try:
        text = (
            ir.files("bioe234_mentor.homeworks.RBSChooser.fixtures")
            .joinpath("sha1_whitelist.csv")
            .read_text(encoding="utf-8")
        )
        _ALLOWED_SHA1_PATH = Path(
            "package:bioe234_mentor/homeworks/RBSChooser/fixtures/sha1_whitelist.csv"
        )
    except Exception:
        path = Path(__file__).resolve().parent.parent / "fixtures" / "sha1_whitelist.csv"
        if path.exists() and path.is_file():
            _ALLOWED_SHA1_PATH = path
            text = path.read_text(encoding="utf-8")
        else:
            _ALLOWED_SHA1_PATH = None
            _ALLOWED_SHA1 = set()
            return _ALLOWED_SHA1

    allowed: set[str] = set()
    for line in text.splitlines():
        s = line.strip()
        s = s.lstrip("\ufeff")
        if not s:
            continue
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
TITLE = "Welcome to the RBSChooser tutorial"
NEXT_STEP = "020"
HASH_MODE = "json"
SUBMIT_STUB = 'mentor.submit_display("PASSCODE", "<your_passcode>")'


def render(state) -> str:
    return (
        "In this tutorial, you will build a function called **RBSChooser2** with help from an LLM.\n\n"
        "This notebook runs one step at a time. Each step shows a single line to run next using `mentor.submit_display(KEY, answer)`.\n"
        "Run the line shown, and the notebook will display the next step.\n\n"
        "To start, enter your passcode. You should have received it by email. If you did not receive it, contact your instructor.\n\n"
        "Paste only the passcode. It must be a single word with letters only."
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
