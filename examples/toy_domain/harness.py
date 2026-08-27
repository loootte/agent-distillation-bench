from __future__ import annotations

from pathlib import Path

from compile_loop.program import load_entrypoint
from compile_loop.types import Program, Task
from toy_domain.tickets import TicketAPI

FAMILY = "close_ticket"
ROOT = Path(__file__).resolve().parent


def make_task(ticket_id: str, resolution: str) -> Task:
    return Task(
        task_id=f"{FAMILY}:{ticket_id}",
        family=FAMILY,
        params={"ticket_id": ticket_id, "resolution": resolution},
        description="Add a resolution comment and close the ticket.",
    )


def env_factory(task: Task) -> TicketAPI:
    api = TicketAPI()
    api.seed_open(str(task.params["ticket_id"]))
    return api


def checker(env: TicketAPI, task: Task) -> bool:
    ticket = env.get_ticket(str(task.params["ticket_id"]))
    resolution = str(task.params["resolution"])
    if ticket["status"] != "closed":
        return False
    return any(resolution in comment["text"] for comment in ticket["comments"])


def load_program_file(path: Path, program_id: str) -> Program:
    return Program(
        program_id=program_id,
        task_family=FAMILY,
        source=path.read_text(encoding="utf-8"),
    )


def replay_success_stub(env: TicketAPI, task: Task) -> None:
    """v0 agent_stub: replay the expected compiled program, not an LLM."""
    program = load_program_file(ROOT / "expected" / "close_ticket.py", "stub")
    load_entrypoint(program)(env, **dict(task.params))
