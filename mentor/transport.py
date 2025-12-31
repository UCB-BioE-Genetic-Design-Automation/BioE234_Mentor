import json
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

from dataclasses import dataclass
from urllib.parse import urljoin

from .config import AUTOGRADER_URL, TIMEOUT_S
from .errors import ServerError

def post_json(payload: Dict[str, Any], url: Optional[str] = None, timeout_s: Optional[int] = None) -> Dict[str, Any]:
    target = (url or AUTOGRADER_URL).strip()
    if not target or target == "REPLACE_WITH_YOUR_WEB_APP_URL":
        raise ServerError("AUTOGRADER_URL is not configured. Set mentor/config.py AUTOGRADER_URL.")

    body_bytes = json.dumps(payload).encode("utf-8")
    timeout = timeout_s or TIMEOUT_S

    def make_req(u: str) -> urllib.request.Request:
        return urllib.request.Request(
            u,
            data=body_bytes,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "BioE234_Mentor/0.1",
            },
            method="POST",
        )

    # Google Apps Script often returns HTTP 302 to a script.googleusercontent.com URL.
    # urllib's default redirect handler will convert POST -> GET for 302/303, breaking the API.
    # So we manually follow at most one redirect and re-POST to the Location.
    def send_once(u: str) -> Dict[str, Any]:
        req = make_req(u)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                ct = resp.headers.get("Content-Type", "")
                raw = resp.read().decode("utf-8", errors="replace")
                if "application/json" not in ct:
                    raise ServerError(f"Expected JSON response, got Content-Type={ct}. Body head: {raw[:400]}")
                try:
                    return json.loads(raw)
                except Exception as e:
                    raise ServerError(f"Failed to parse JSON. Body head: {raw[:400]}") from e
        except urllib.error.HTTPError as e:
            # Handle redirects explicitly.
            if e.code in (301, 302, 303, 307, 308):
                loc = e.headers.get("Location")
                if loc:
                    return {"__redirect__": urljoin(u, loc)}

            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                body = ""
            raise ServerError(f"HTTPError {e.code}. Content-Type={e.headers.get('Content-Type','')}. Body head: {body[:800]}") from e
        except urllib.error.URLError as e:
            raise ServerError(f"URLError: {e}") from e

    first = send_once(target)
    if isinstance(first, dict) and "__redirect__" in first:
        redirected = first["__redirect__"]
        second = send_once(redirected)
        if isinstance(second, dict) and "__redirect__" in second:
            raise ServerError(f"Unexpected second redirect to {second['__redirect__']}")
        return second

    return first
