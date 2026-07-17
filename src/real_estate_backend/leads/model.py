from __future__ import annotations
import enum
from sqlalchemy import DateTime, ForeignKey, Text, Enum as SAEnum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from real_estate_backend.customers.model import Customer
    from real_estate_backend.properties.model import Property
from real_estate_backend.core.database import Base

class LeadStatus(str,enum.Enum):
    NEW="new",
    CONTACTED="contacted",
    QUALIFIED="qualified",
    CLOSED="closed",
    LOST="lost"
    
class Lead(Base):
    __tablename__="leads"
    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    
    customer_id:Mapped[int]=mapped_column(ForeignKey("customers.id"),nullable=False,index=True)
    property_id:Mapped[int]=mapped_column(ForeignKey("properties.id"),nullable=False,index=True)
    status:Mapped[LeadStatus]=mapped_column(SAEnum(LeadStatus),default=LeadStatus.NEW,nullable=False)
    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    notes:Mapped[str]=mapped_column(String,nullable=True)
    created_at:Mapped[DateTime]=mapped_column(DateTime,server_default=func.now())
    updated_at:Mapped[DateTime]=mapped_column(DateTime,server_default=func.now(),onupdate=func.now())
    
    customer:Mapped[Customer]=relationship("Customer",back_populates="leads")
    property:Mapped[Property]=relationship("Property",back_populates="leads")