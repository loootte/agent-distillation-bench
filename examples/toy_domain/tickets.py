"""Fixed ticket API. State is fully observable; success is machine-checkable."""

from __future__ import annotations

from typing import Any

TRANSITIONS = {
    "open": ("in_progress", "closed"),
    "in_progress": ("resolved", "open"),
    "resolved": ("closed", "in_progress"),
    "closed": (),
}


class TicketError(Exception):
    pass


class TicketAPI:
    def __init__(self) -> None:
        self._tickets: dict[str, dict[str, Any]] = {}

    def seed_open(self, ticket_id: str, title: str = "incident") -> dict[str, Any]:
        ticket = {
            "id": ticket_id,
            "title": title,
            "status": "open",
            "comments": [],
        }
        self._tickets[ticket_id] = ticket
        return self.get_ticket(ticket_id)

    def get_ticket(self, ticket_id: str) -> dict[str, Any]:
        if ticket_id not in self._tickets:
            raise TicketError(f"unknown ticket: {ticket_id}")
        ticket = self._tickets[ticket_id]
        return {
            "id": ticket["id"],
            "title": ticket["title"],
            "status": ticket["status"],
            "comments": [dict(c) for c in ticket["comments"]],
        }

    def add_comment(self, ticket_id: str, resolution: str) -> dict[str, Any]:
        ticket = self._require(ticket_id)
        ticket["comments"].append({"text": resolution})
        return self.get_ticket(ticket_id)

    def transition(self, ticket_id: str, status: str) -> dict[str, Any]:
        ticket = self._require(ticket_id)
        allowed = TRANSITIONS[ticket["status"]]
        if status not in allowed:
            raise TicketError(
                f"cannot {ticket['status']} -> {status} on {ticket_id}"
            )
        ticket["status"] = status
        return self.get_ticket(ticket_id)

    def snapshot(self, ticket_id: str) -> dict[str, Any]:
        return {"ticket": self.get_ticket(ticket_id)}

    def _require(self, ticket_id: str) -> dict[str, Any]:
        if ticket_id not in self._tickets:
            raise TicketError(f"unknown ticket: {ticket_id}")
        return self._tickets[ticket_id]
