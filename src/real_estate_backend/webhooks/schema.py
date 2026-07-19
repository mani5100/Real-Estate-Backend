from pydantic import BaseModel
from real_estate_backend.leads.model import LeadStatus
from typing import Optional


class WebhookPayload(BaseModel):
    customer_id: int
    property_id: int
    status: LeadStatus = LeadStatus.NEW
    agent_id: Optional[int] = None
    notes: Optional[str] = None


class WebhookResponse(BaseModel):
    received: bool = True
    action: str   # "created" or "updated"
    lead_id: int