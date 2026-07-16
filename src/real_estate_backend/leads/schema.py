from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from real_estate_backend.leads.model import LeadStatus
from real_estate_backend.customers.schema import CustomerResponse
from real_estate_backend.properties.schema import PropertyResponse


class LeadBase(BaseModel):
    customer_id: int
    property_id: int
    status: LeadStatus = LeadStatus.NEW
    agent_id: Optional[str] = None
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    agent_id: Optional[str] = None
    notes: Optional[str] = None


class LeadResponse(LeadBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadDetailResponse(LeadResponse):
    customer: CustomerResponse
    property: PropertyResponse