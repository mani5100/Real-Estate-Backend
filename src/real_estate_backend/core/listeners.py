import asyncio

from real_estate_backend.core.event_bus import event_bus
from real_estate_backend.core.events import LeadStatusChangedEvent, LeadCreatedEvent
from real_estate_backend.core.logging import logger
from real_estate_backend.leads.model import LeadStatus
from real_estate_backend.core.websocket_manager import ws_manager


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
    
@event_bus.on("lead.status.changed")
def handle_websocket_broadcast(event: LeadStatusChangedEvent) -> None:
    """
    Pushes status change to all WebSocket clients watching this lead.
    Uses asyncio to run async broadcast from sync listener.
    """
    message = {
        "type": "status_changed",
        "lead_id": event.lead_id,
        "old_status": event.old_status,
        "new_status": event.new_status,
        "agent_id": event.agent_id,
    }

    try:
        loop = asyncio.get_event_loop()
        loop.create_task(ws_manager.broadcast(event.lead_id, message))
    except RuntimeError:
        asyncio.run(ws_manager.broadcast(event.lead_id, message))
        
@event_bus.on("lead.created")
def handle_lead_created_notification(event: LeadCreatedEvent) -> None:
    """
    Fires when a customer clicks Interested on a property.
    Notifies the agent who owns that property.
    Currently logs — real email/push goes here later.
    """
    logger.info(
        "NOTIFICATION: New lead created — notify agent",
        extra={
            "lead_id": event.lead_id,
            "customer_id": event.customer_id,
            "property_id": event.property_id,
            "agent_id": event.agent_id,
            "notification": "Email/push to agent would be sent here",
        }
    )