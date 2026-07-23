from pydantic.fields import Field

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Annotated, Optional
from real_estate_backend.core.enums import PaymentMethod
from real_estate_backend.leads.model import LeadStatus
from real_estate_backend.customers.schema import CustomerResponse
from real_estate_backend.properties.schema import PropertyResponse


class LeadBase(BaseModel):
    customer_id: int
    property_id: int
    status: LeadStatus = LeadStatus.NEW
    agent_id: Optional[int] = None
    budget: Optional[int] = None
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    status: Optional[LeadStatus] = None
    agent_id: Optional[int] = None
    budget: Optional[int] = None
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = None


class LeadResponse(LeadBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LeadDetailResponse(LeadResponse):
    customer: CustomerResponse
    property: PropertyResponse
    
class LeadPaginatedResponse(BaseModel):
    total: int
    next_cursor: int | None
    results: list[LeadResponse]
    
class InterestedRequest(BaseModel):
    budget: Optional[Annotated[int, Field(gt=0)]] = None
    payment_method: Optional[PaymentMethod] = None
    notes: Optional[str] = None
    
    
