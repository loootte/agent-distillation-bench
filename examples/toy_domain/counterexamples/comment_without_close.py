def run(api, ticket_id, resolution):
    """Lossy program: every step succeeds, the ticket is still open."""
    api.add_comment(ticket_id, resolution=resolution)
