from __future__ import annotations

from compile_loop.program import execute_program
from compile_loop.types import Checker, EnvFactory, Program, Task, VerifyResult


class VerifyBeforeStore:
    """Replay P from a clean initial state, then ask an independent checker.

    Coverage (the program ran to the last step) is not completion.
    A program that comments but never closes the ticket must be rejected.
    """

    def verify(
        self,
        program: Program,
        task: Task,
        env_factory: EnvFactory,
        checker: Checker,
    ) -> VerifyResult:
        env = env_factory(task)
        try:
            execute_program(program, env, task)
        except Exception as exc:  # noqa: BLE001 — surface any replay failure
            return VerifyResult(
                accepted=False,
                replay_ok=False,
                task_ok=False,
                reason="replay_error",
                replay_error=f"{type(exc).__name__}: {exc}",
            )

        task_ok = bool(checker(env, task))
        if task_ok:
            return VerifyResult(
                accepted=True,
                replay_ok=True,
                task_ok=True,
                reason="accepted",
            )
        return VerifyResult(
            accepted=False,
            replay_ok=True,
            task_ok=False,
            reason="lossy_program",
        )
