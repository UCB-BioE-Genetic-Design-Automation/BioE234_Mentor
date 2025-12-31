from typing import Any, Dict, Optional

from .transport import post_json
from .protocol import parse_response, MentorResponse
from .display import show
from .tasks import run_client_task

def submit(passkey: str, assignment: str, submission: Optional[Any] = None, artifacts: Optional[Dict[str, Any]] = None) -> MentorResponse:
    payload: Dict[str, Any] = {
        "passkey": passkey,
        "assignment": assignment,
        "submission": submission,
    }
    if artifacts is not None:
        payload["artifacts"] = artifacts

    raw = post_json(payload)
    resp = parse_response(raw)
    show(resp)

    if resp.step.client_task:
        produced = run_client_task(resp.step.client_task)
        raw2 = post_json({
            "passkey": passkey,
            "assignment": assignment,
            "submission": submission,
            "artifacts": produced,
        })
        resp2 = parse_response(raw2)
        show(resp2)
        return resp2

    return resp
