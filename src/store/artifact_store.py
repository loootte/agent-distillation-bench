from __future__ import annotations

from compile_loop.types import Program, VerifyResult


class MemoryArtifactStore:
    """In-memory store. put() is for verified programs only."""

    def __init__(self) -> None:
        self._programs: dict[str, Program] = {}
        self.rejections: list[tuple[Program, VerifyResult]] = []

    def hit(self, task_family: str) -> bool:
        return task_family in self._programs

    def get(self, task_family: str) -> Program | None:
        return self._programs.get(task_family)

    def put(self, program: Program) -> None:
        self._programs[program.task_family] = program

    def reject(self, program: Program, result: VerifyResult) -> None:
        self.rejections.append((program, result))
