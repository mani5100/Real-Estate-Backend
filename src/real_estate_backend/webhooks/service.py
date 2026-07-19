from sqlalchemy.orm import Session
from sqlalchemy import select
from real_estate_backend.leads.model import Lead
from real_estate_backend.webhooks.schema import WebhookPayload
from real_estate_backend.core.exceptions import (
    CustomerNotFoundError,
    PropertyNotFoundError,
)
from real_estate_backend.customers.model import Customer
from real_estate_backend.properties.model import Property
from real_estate_backend.core.logging import logger, log_call
from real_estate_backend.core.event_bus import event_bus
from real_estate_backend.core.events import LeadStatusChangedEvent


@log_call
def upsert_lead_from_webhook(db: Session, payload: WebhookPayload) -> tuple[Lead, str]:
    """
    Upsert = Update or Insert.

    Checks if lead exists for this customer + property combo:
    - Found  → update status/notes → action="updated"
    - Not found → create new lead  → action="created"

    Returns (lead, action) tuple.
    """
    customer = db.get(Customer, payload.customer_id)
    if not customer:
        raise CustomerNotFoundError(payload.customer_id)

    prop = db.get(Property, payload.property_id)
    if not prop:
        raise PropertyNotFoundError(payload.property_id)

    existing_lead = db.scalar(
        select(Lead).where(
            Lead.customer_id == payload.customer_id,
            Lead.property_id == payload.property_id,
        )
    )

    if existing_lead:
        old_status = existing_lead.status
        existing_lead.status = payload.status
        if payload.notes:
            existing_lead.notes = payload.notes
        if payload.agent_id:
            existing_lead.agent_id = payload.agent_id

        db.commit()
        db.refresh(existing_lead)

        if old_status != payload.status:
            event_bus.emit(
                "lead.status.changed",
                LeadStatusChangedEvent(
                    lead_id=existing_lead.id,
                    customer_id=existing_lead.customer_id,
                    property_id=existing_lead.property_id,
                    old_status=old_status,
                    new_status=existing_lead.status,
                    agent_id=existing_lead.agent_id,
                )
            )

        logger.info("Webhook updated existing lead", extra={
            "lead_id": existing_lead.id,
            "old_status": old_status,
            "new_status": payload.status,
        })
        return existing_lead, "updated"

    else:
        new_lead = Lead(
            customer_id=payload.customer_id,
            property_id=payload.property_id,
            status=payload.status,
            agent_id=payload.agent_id,
            notes=payload.notes,
        )
        db.add(new_lead)
        db.commit()
        db.refresh(new_lead)

        logger.info("Webhook created new lead", extra={
            "lead_id": new_lead.id,
            "customer_id": payload.customer_id,
            "property_id": payload.property_id,
        })
        return new_lead, "created"