def run(api, ticket_id, resolution):
    """Faithful program: comment and drive the ticket to closed."""
    ticket = api.get_ticket(ticket_id)
    if ticket["status"] == "open":
        api.transition(ticket_id, status="in_progress")
    api.add_comment(ticket_id, resolution=resolution)
    ticket = api.get_ticket(ticket_id)
    if ticket["status"] == "in_progress":
        api.transition(ticket_id, status="resolved")
    ticket = api.get_ticket(ticket_id)
    if ticket["status"] == "resolved":
        api.transition(ticket_id, status="closed")
