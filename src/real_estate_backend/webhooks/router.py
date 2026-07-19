import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from real_estate_backend.core.database import get_db
from real_estate_backend.core.webhook_security import validate_webhook_signature
from real_estate_backend.webhooks.schema import WebhookPayload, WebhookResponse
from real_estate_backend.webhooks import service
from real_estate_backend.core.logging import logger

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/inbound", response_model=WebhookResponse)
async def inbound_webhook(
    db: Session = Depends(get_db),
    raw_body: bytes = Depends(validate_webhook_signature),
):
    """
    Receives inbound webhook from external service.
    """
    
    payload_dict = json.loads(raw_body)
    payload = WebhookPayload(**payload_dict)

    logger.info("Webhook inbound received", extra={
        "customer_id": payload.customer_id,
        "property_id": payload.property_id,
        "status": payload.status,
    })

    lead, action = service.upsert_lead_from_webhook(db, payload)

    return WebhookResponse(
        received=True,
        action=action,
        lead_id=lead.id,
    )