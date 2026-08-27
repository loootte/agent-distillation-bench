from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_ROOT / "src"), str(_ROOT / "examples")]

from compile.compiler import LinearizingCompiler
from compile_loop.schema import load_jsonl_traces
from runtime.scheduler import Scheduler
from store.artifact_store import MemoryArtifactStore
from toy_domain.harness import (
    checker,
    env_factory,
    load_program_file,
    make_task,
    replay_success_stub,
)

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "examples" / "toy_domain"


class RuntimeLoopTests(unittest.TestCase):
    def test_ingest_rejects_lossy_then_fallback_succeeds(self) -> None:
        store = MemoryArtifactStore()
        sched = Scheduler(
            store=store,
            env_factory=env_factory,
            checker=checker,
            agent_stub=replay_success_stub,
        )
        task = make_task("T-700", "nacked the poison message")
        lossy = load_program_file(
            TOY / "counterexamples" / "comment_without_close.py",
            "lossy",
        )
        result = sched.ingest(lossy, task)
        self.assertFalse(result.accepted)
        self.assertFalse(store.hit(task.family))

        run = sched.run(task)
        self.assertTrue(run.fallback)
        self.assertTrue(run.task_ok)
        self.assertFalse(run.used_program)

    def test_verified_program_is_replayed(self) -> None:
        store = MemoryArtifactStore()
        sched = Scheduler(
            store=store,
            env_factory=env_factory,
            checker=checker,
            agent_stub=replay_success_stub,
        )
        seed = make_task("T-800", "cleared the deadlock")
        good = load_program_file(TOY / "expected" / "close_ticket.py", "good")
        self.assertTrue(sched.ingest(good, seed).accepted)

        warm = make_task("T-801", "cleared the deadlock")
        run = sched.run(warm)
        self.assertTrue(run.used_program)
        self.assertFalse(run.fallback)
        self.assertTrue(run.task_ok)

    def test_linearizing_compiler_output_passes_the_gate(self) -> None:
        traces = load_jsonl_traces(TOY / "traces.jsonl")
        program = LinearizingCompiler().compile(traces, "close_ticket")
        store = MemoryArtifactStore()
        sched = Scheduler(
            store=store,
            env_factory=env_factory,
            checker=checker,
            agent_stub=replay_success_stub,
        )
        task = make_task("T-900", "disk full; reclaimed inode table")
        result = sched.ingest(program, task)
        self.assertTrue(result.accepted, (result, program.source))


if __name__ == "__main__":
    unittest.main()
