from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence


@dataclass(frozen=True)
class TraceStep:
    task_id: str
    step: int
    observation: Mapping[str, Any]
    action: str
    tool: str | None
    args: Mapping[str, Any]
    success: bool
    episode_id: str = ""
    task_family: str = ""
    error: str | None = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "TraceStep":
        return cls(
            task_id=str(raw["task_id"]),
            step=int(raw["step"]),
            observation=dict(raw.get("observation") or {}),
            action=str(raw["action"]),
            tool=raw.get("tool"),
            args=dict(raw.get("args") or {}),
            success=bool(raw["success"]),
            episode_id=str(raw.get("episode_id") or ""),
            task_family=str(raw.get("task_family") or ""),
            error=raw.get("error"),
        )


@dataclass(frozen=True)
class Task:
    """One concrete task instance in a family."""

    task_id: str
    family: str
    params: Mapping[str, Any]
    description: str = ""


@dataclass
class Program:
    """Deterministic artifact: parameterized Python, optional state-machine IR."""

    program_id: str
    task_family: str
    source: str
    entrypoint: str = "run"
    language: str = "python"
    state_machine: Mapping[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "program_id": self.program_id,
            "task_family": self.task_family,
            "source": self.source,
            "entrypoint": self.entrypoint,
            "language": self.language,
            "state_machine": self.state_machine,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Program":
        return cls(
            program_id=str(raw["program_id"]),
            task_family=str(raw["task_family"]),
            source=str(raw["source"]),
            entrypoint=str(raw.get("entrypoint") or "run"),
            language=str(raw.get("language") or "python"),
            state_machine=raw.get("state_machine"),
            metadata=dict(raw.get("metadata") or {}),
        )


@dataclass(frozen=True)
class VerifyResult:
    accepted: bool
    replay_ok: bool
    task_ok: bool
    reason: str
    replay_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "replay_ok": self.replay_ok,
            "task_ok": self.task_ok,
            "reason": self.reason,
            "replay_error": self.replay_error,
        }


@dataclass(frozen=True)
class RunResult:
    used_program: bool
    fallback: bool
    task_ok: bool
    guard_miss: bool = False
    detail: str = ""


class Compiler(Protocol):
    def compile(self, traces: Sequence[TraceStep], task_family: str) -> Program:
        """Turn successful traces of one family into a candidate Program."""


class Checker(Protocol):
    def __call__(self, env: Any, task: Task) -> bool:
        """Independent success predicate. Must not trust the program's own return value."""


class EnvFactory(Protocol):
    def __call__(self, task: Task) -> Any:
        """Fresh environment in the task's clean initial state."""


class Verifier(Protocol):
    def verify(
        self,
        program: Program,
        task: Task,
        env_factory: EnvFactory,
        checker: Checker,
    ) -> VerifyResult:
        """Replay P on a clean env; accept only if checker says the task is done."""


class ArtifactStore(Protocol):
    def hit(self, task_family: str) -> bool: ...
    def get(self, task_family: str) -> Program | None: ...
    def put(self, program: Program) -> None: ...
    def reject(self, program: Program, result: VerifyResult) -> None: ...
