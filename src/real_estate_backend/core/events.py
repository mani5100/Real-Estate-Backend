from dataclasses import dataclass
from real_estate_backend.leads.model import LeadStatus


@dataclass
class LeadStatusChangedEvent:
    lead_id: int
    customer_id: int
    property_id: int
    old_status: LeadStatus
    new_status: LeadStatus
    agent_id: str | None