from __future__ import annotations

from typing import Any, Callable, Mapping

from compile_loop.types import Program, Task


def load_entrypoint(program: Program) -> Callable[..., Any]:
    if program.language != "python":
        raise ValueError(f"unsupported language: {program.language}")
    namespace: dict[str, Any] = {}
    exec(compile(program.source, f"<{program.program_id}>", "exec"), namespace)
    fn = namespace.get(program.entrypoint)
    if not callable(fn):
        raise ValueError(f"entrypoint {program.entrypoint!r} not found in program")
    return fn


def execute_program(program: Program, env: Any, task: Task) -> Any:
    fn = load_entrypoint(program)
    params: Mapping[str, Any] = task.params
    return fn(env, **dict(params))
