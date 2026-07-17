from real_estate_backend.core.event_bus import event_bus
from real_estate_backend.core.events import LeadStatusChangedEvent
from real_estate_backend.core.logging import logger
from real_estate_backend.leads.model import LeadStatus


@event_bus.on("lead.status.changed")
def handle_lead_status_notification(event: LeadStatusChangedEvent) -> None:
    """Simulates sending a notification when lead reaches terminal state."""
    terminal_states = {LeadStatus.CLOSED, LeadStatus.LOST}

    if event.new_status in terminal_states:
        logger.info(
            "NOTIFICATION: Lead reached terminal state",
            extra={
                "lead_id": event.lead_id,
                "customer_id": event.customer_id,
                "old_status": event.old_status,
                "new_status": event.new_status,
                "agent_id": event.agent_id,
                "notification": "Email/SMS would be sent here",
            }
        )


@event_bus.on("lead.status.changed")
def handle_lead_status_audit(event: LeadStatusChangedEvent) -> None:
    """Logs every status change for audit trail."""
    logger.info(
        "AUDIT: Lead status changed",
        extra={
            "lead_id": event.lead_id,
            "old_status": event.old_status,
            "new_status": event.new_status,
            "agent_id": event.agent_id,
        }
        )