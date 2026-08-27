from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from compile_loop.types import TraceStep

REQUIRED_FIELDS = (
    "task_id",
    "step",
    "observation",
    "action",
    "tool",
    "args",
    "success",
)


def validate_trace_step(raw: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REQUIRED_FIELDS:
        if field not in raw:
            errors.append(f"missing field: {field}")
    if errors:
        return errors
    if not isinstance(raw["task_id"], str) or not raw["task_id"]:
        errors.append("task_id must be a non-empty string")
    if not isinstance(raw["step"], int) or isinstance(raw["step"], bool) or raw["step"] < 0:
        errors.append("step must be an integer >= 0")
    if not isinstance(raw["observation"], dict):
        errors.append("observation must be an object")
    if not isinstance(raw["action"], str):
        errors.append("action must be a string")
    if raw["tool"] is not None and not isinstance(raw["tool"], str):
        errors.append("tool must be a string or null")
    if not isinstance(raw["args"], dict):
        errors.append("args must be an object")
    if not isinstance(raw["success"], bool):
        errors.append("success must be a boolean")
    return errors


def load_jsonl_traces(path: str | Path) -> list[TraceStep]:
    steps: list[TraceStep] = []
    with Path(path).open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            raw = json.loads(line)
            errors = validate_trace_step(raw)
            if errors:
                raise ValueError(f"{path}:{line_no}: {'; '.join(errors)}")
            steps.append(TraceStep.from_dict(raw))
    return steps
