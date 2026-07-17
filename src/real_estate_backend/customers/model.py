from __future__ import annotations
from sqlalchemy import Boolean, DateTime, String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from real_estate_backend.core.database import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from real_estate_backend.leads.model import Lead

class Customer(Base):
    __tablename__="customers"
    
    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    full_name:Mapped[str]=mapped_column(String(100),nullable=False)
    email:Mapped[str]=mapped_column(String(100),unique=True,nullable=False)
    phone:Mapped[str]=mapped_column(String(20),nullable=False)
    is_active:Mapped[bool]=mapped_column(Boolean,default=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, unique=True
    )
    created_at:Mapped[DateTime]=mapped_column(DateTime,server_default=func.now())
    updated_at:Mapped[DateTime]=mapped_column(DateTime,server_default=func.now(),onupdate=func.now())
    
    leads:Mapped[list[Lead]]=relationship("Lead",back_populates="customer")
    