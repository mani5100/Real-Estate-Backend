from __future__ import annotations
from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from real_estate_backend.leads.model import Lead
from real_estate_backend.core.database import Base
class Property(Base):
    __tablename__="properties"
    
    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    title:Mapped[str]=mapped_column(String(30),nullable=False)
    city:Mapped[str]=mapped_column(String(20),nullable=False,index=True)
    address:Mapped[str]=mapped_column(String(100),nullable=False)
    price:Mapped[int]=mapped_column(Integer,nullable=False)
    bedrooms:Mapped[int]=mapped_column(Integer,default=1)
    bathrooms:Mapped[int]=mapped_column(Integer,default=1)
    area_sqft:Mapped[float]=mapped_column(Float,nullable=True)
    description:Mapped[int]=mapped_column(Integer,nullable=True)
    is_available:Mapped[bool]=mapped_column(Boolean,default=True)
    created_at:Mapped[DateTime]=mapped_column(DateTime,server_default=func.now())
    updated_at:Mapped[DateTime]=mapped_column(DateTime,server_default=func.now(),onupdate=func.now())
    
    leads:Mapped[list[Lead]]=relationship("Lead",back_populates="property")