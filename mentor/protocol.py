from dataclasses import dataclass
from typing import Any, Dict, Optional

from .errors import ProtocolError

@dataclass(frozen=True)
class Step:
    slug: str
    prompt: str
    submission_schema: Optional[Dict[str, Any]] = None
    client_task: Optional[Dict[str, Any]] = None

@dataclass(frozen=True)
class MentorResponse:
    ok: bool
    assignment: str
    state: str
    step: Step
    feedback: Optional[str] = None

def parse_response(obj: Dict[str, Any]) -> MentorResponse:
    if not isinstance(obj, dict):
        raise ProtocolError("Response is not a JSON object")

    if obj.get("ok") is not True:
        err = obj.get("error") or "Server returned ok=false"
        raise ProtocolError(str(err))

    assignment = obj.get("assignment")
    if not assignment:
        raise ProtocolError("Missing 'assignment' in response")

    step_obj = obj.get("step")
    if not isinstance(step_obj, dict):
        raise ProtocolError("Missing or invalid 'step' in response")

    slug = step_obj.get("slug")
    prompt = step_obj.get("prompt")
    if not slug or not isinstance(slug, str):
        raise ProtocolError("Missing/invalid step.slug")
    if prompt is None or not isinstance(prompt, str):
        raise ProtocolError("Missing/invalid step.prompt")

    state = obj.get("state")
    if not state or not isinstance(state, str):
        raise ProtocolError("Missing/invalid 'state' in response")

    feedback = obj.get("feedback")
    if feedback is not None and not isinstance(feedback, str):
        feedback = str(feedback)

    submission_schema = step_obj.get("submission_schema")
    if submission_schema is not None and not isinstance(submission_schema, dict):
        submission_schema = None

    client_task = step_obj.get("client_task")
    if client_task is not None and not isinstance(client_task, dict):
        client_task = None

    return MentorResponse(
        ok=True,
        assignment=assignment,
        state=state,
        step=Step(
            slug=slug,
            prompt=prompt,
            submission_schema=submission_schema,
            client_task=client_task,
        ),
        feedback=feedback,
    )
