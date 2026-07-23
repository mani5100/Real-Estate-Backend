from __future__ import annotations
from sqlalchemy import Boolean, DateTime, String, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from real_estate_backend.core.database import Base
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from real_estate_backend.leads.model import Lead
    from real_estate_backend.users.model import User

class Customer(Base):
    __tablename__="customers"
    
    id:Mapped[int]=mapped_column(primary_key=True,index=True)
    phone:Mapped[str]=mapped_column(String(20),nullable=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )
    created_at:Mapped[DateTime]=mapped_column(DateTime,server_default=func.now())
    updated_at:Mapped[DateTime]=mapped_column(DateTime,server_default=func.now(),onupdate=func.now())
    
    user: Mapped[User] = relationship(
        "User",
        back_populates="customer_profile",
    )
    leads:Mapped[list[Lead]]=relationship("Lead",back_populates="customer")
    