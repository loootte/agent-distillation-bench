from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(_ROOT / "src"), str(_ROOT / "examples")]

from compile_loop.schema import load_jsonl_traces, validate_trace_step

ROOT = Path(__file__).resolve().parents[1]


class TraceSchemaTests(unittest.TestCase):
    def test_toy_traces_validate_and_load(self) -> None:
        steps = load_jsonl_traces(ROOT / "examples" / "toy_domain" / "traces.jsonl")
        self.assertEqual(len(steps), 12)
        families = {s.task_family for s in steps}
        self.assertEqual(families, {"close_ticket"})
        episodes = {s.episode_id for s in steps}
        self.assertEqual(episodes, {"ep-001", "ep-002", "ep-003"})
        self.assertTrue(all(s.success for s in steps))

    def test_missing_required_field(self) -> None:
        raw = {
            "task_id": "x",
            "step": 0,
            "observation": {},
            "action": "noop",
            "tool": None,
            "args": {},
        }
        errors = validate_trace_step(raw)
        self.assertTrue(any("success" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
