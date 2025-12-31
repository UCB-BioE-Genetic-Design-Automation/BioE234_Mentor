from typing import Optional
from .protocol import MentorResponse

def show(resp: MentorResponse) -> None:
    if resp.feedback:
        print(resp.feedback)
        print()
    print(resp.step.prompt)

def show_state(resp: MentorResponse) -> None:
    print(f"[{resp.assignment}] step={resp.step.slug} state={resp.state}")
