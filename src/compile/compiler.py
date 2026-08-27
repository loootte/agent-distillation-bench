from __future__ import annotations

import json
from collections import defaultdict
from typing import Any, Sequence

from compile_loop.types import Program, TraceStep


def _literal(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


class LinearizingCompiler:
    """v0 compiler: parameterize one successful episode's tool sequence.

    Not a research-grade aligner. Issue #3 should replace this with
    cross-trace subgraph compilation. The interface (`compile`) stays.
    """

    min_success_episodes: int = 1

    def __init__(self, param_names: Sequence[str] = ("ticket_id", "resolution")) -> None:
        self.param_names = tuple(param_names)

    def compile(self, traces: Sequence[TraceStep], task_family: str) -> Program:
        episodes = _group_successful_episodes(traces, task_family)
        if len(episodes) < self.min_success_episodes:
            raise ValueError(
                f"{task_family}: need >= {self.min_success_episodes} successful "
                f"episodes, got {len(episodes)}"
            )
        _episode_id, steps = next(iter(episodes.items()))
        source, sm = self._emit_python(steps)
        return Program(
            program_id=f"{task_family}:linearized",
            task_family=task_family,
            source=source,
            state_machine=sm,
            metadata={
                "compiler": "linearizing-v0",
                "source_episode": steps[0].episode_id if steps else "",
                "n_success_episodes": len(episodes),
            },
        )

    def _emit_python(self, steps: Sequence[TraceStep]) -> tuple[str, dict[str, Any]]:
        params = ", ".join(self.param_names)
        calls: list[str] = []
        transitions: list[dict[str, Any]] = []
        for step in steps:
            if not step.tool:
                continue
            args_items = []
            for name, value in step.args.items():
                if name in self.param_names:
                    args_items.append(f"{name}={name}")
                else:
                    args_items.append(f"{name}={_literal(value)}")
            joined = ", ".join(args_items)
            calls.append(f"    api.{step.tool}({joined})")
            transitions.append(
                {
                    "from_predicate": dict(step.observation),
                    "tool": step.tool,
                    "args": dict(step.args),
                }
            )
        body = "\n".join(calls) if calls else "    pass"
        source = (
            f"def run(api, {params}):\n"
            '    """Compiled from a successful episode."""\n'
            f"{body}\n"
        )
        return source, {"kind": "linear", "transitions": transitions}


def _group_successful_episodes(
    traces: Sequence[TraceStep], task_family: str
) -> dict[str, list[TraceStep]]:
    grouped: dict[str, list[TraceStep]] = defaultdict(list)
    for step in traces:
        family = step.task_family or step.task_id.split(":", 1)[0]
        if family != task_family:
            continue
        if not step.success:
            continue
        key = step.episode_id or step.task_id
        grouped[key].append(step)
    for key in grouped:
        grouped[key].sort(key=lambda s: s.step)
    return dict(grouped)
