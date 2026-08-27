from __future__ import annotations

from typing import Callable

from compile_loop.program import execute_program
from compile_loop.types import (
    ArtifactStore,
    Checker,
    EnvFactory,
    Program,
    RunResult,
    Task,
    VerifyResult,
)
from verify.verifier import VerifyBeforeStore

Guard = Callable[[Program, Task, object], bool]
AgentStub = Callable[[object, Task], None]


class Scheduler:
    """if store.hit(task) and guards_ok: run(P) else: run(agent_stub)."""

    def __init__(
        self,
        store: ArtifactStore,
        env_factory: EnvFactory,
        checker: Checker,
        agent_stub: AgentStub,
        guard: Guard | None = None,
        verifier: VerifyBeforeStore | None = None,
    ) -> None:
        self.store = store
        self.env_factory = env_factory
        self.checker = checker
        self.agent_stub = agent_stub
        self.guard = guard or (lambda _program, _task, _env: True)
        self.verifier = verifier or VerifyBeforeStore()

    def ingest(self, program: Program, task: Task) -> VerifyResult:
        result = self.verifier.verify(program, task, self.env_factory, self.checker)
        if result.accepted:
            self.store.put(program)
        else:
            self.store.reject(program, result)
        return result

    def run(self, task: Task) -> RunResult:
        env = self.env_factory(task)
        program = self.store.get(task.family)
        if program is not None and self.guard(program, task, env):
            try:
                execute_program(program, env, task)
            except Exception as exc:  # noqa: BLE001
                self.agent_stub(env, task)
                return RunResult(
                    used_program=False,
                    fallback=True,
                    task_ok=bool(self.checker(env, task)),
                    guard_miss=True,
                    detail=f"program_error:{type(exc).__name__}",
                )
            return RunResult(
                used_program=True,
                fallback=False,
                task_ok=bool(self.checker(env, task)),
                detail="replay",
            )

        self.agent_stub(env, task)
        return RunResult(
            used_program=False,
            fallback=True,
            task_ok=bool(self.checker(env, task)),
            guard_miss=program is not None,
            detail="stub",
        )
