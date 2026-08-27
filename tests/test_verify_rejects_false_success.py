"""The verify-before-store gate must reject programs that run but do not finish the task."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_ROOT / "src"), str(_ROOT / "examples")]

from store.artifact_store import MemoryArtifactStore
from toy_domain.harness import checker, env_factory, load_program_file, make_task
from verify.verifier import VerifyBeforeStore

ROOT = Path(__file__).resolve().parents[1]
TOY = ROOT / "examples" / "toy_domain"


class VerifyGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = make_task("T-999", "patched the leak")
        self.verifier = VerifyBeforeStore()

    def test_rejects_comment_without_close(self) -> None:
        program = load_program_file(
            TOY / "counterexamples" / "comment_without_close.py",
            "lossy",
        )
        result = self.verifier.verify(program, self.task, env_factory, checker)
        self.assertTrue(result.replay_ok, result)
        self.assertFalse(result.task_ok, result)
        self.assertFalse(result.accepted, result)
        self.assertEqual(result.reason, "lossy_program")

    def test_lossy_program_is_not_stored(self) -> None:
        program = load_program_file(
            TOY / "counterexamples" / "comment_without_close.py",
            "lossy",
        )
        store = MemoryArtifactStore()
        result = self.verifier.verify(program, self.task, env_factory, checker)
        store.reject(program, result)
        self.assertFalse(store.hit(self.task.family))
        self.assertIsNone(store.get(self.task.family))
        self.assertEqual(len(store.rejections), 1)

    def test_accepts_faithful_close_ticket_program(self) -> None:
        program = load_program_file(TOY / "expected" / "close_ticket.py", "good")
        result = self.verifier.verify(program, self.task, env_factory, checker)
        self.assertTrue(result.accepted, result)
        self.assertTrue(result.replay_ok)
        self.assertTrue(result.task_ok)


if __name__ == "__main__":
    unittest.main()
