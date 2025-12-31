from typing import Any, Dict
from .errors import TaskError

def run_client_task(task: Dict[str, Any]) -> Dict[str, Any]:
    kind = str(task.get("kind") or "").strip()
    if not kind:
        raise TaskError("client_task missing 'kind'")

    if kind == "python_tests":
        tests = task.get("tests")
        if not isinstance(tests, list):
            raise TaskError("python_tests requires 'tests' as a list")
        results: Dict[str, Any] = {}
        for test_id in tests:
            results[str(test_id)] = {"ok": False, "error": "Not implemented"}
        return {"tests": results}

    raise TaskError(f"Unknown client_task kind: {kind}")
