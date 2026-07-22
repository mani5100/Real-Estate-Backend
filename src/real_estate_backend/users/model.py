from __future__ import annotations
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from real_estate_backend.core.database import Base
from real_estate_backend.core.enums import UserRole
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from real_estate_backend.customers.model import Customer
    from real_estate_backend.agents.model import AgentProfile, AgentApplication


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)  # hashed
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(
    SAEnum(UserRole, name="userrole"),
    nullable=False,
    default=UserRole.USER,
    server_default="USER",
)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    customer_profile: Mapped[Customer | None] = relationship(
    "Customer",
    back_populates="user",
    uselist=False,
    cascade="all, delete-orphan",
    passive_deletes=True,
)
    agent_profile: Mapped[AgentProfile | None] = relationship(
    "AgentProfile",
    back_populates="user",
    uselist=False,
    cascade="all, delete-orphan",
    passive_deletes=True,
)
    agent_application: Mapped[AgentApplication | None] = relationship(
    "AgentApplication",
    back_populates="user",
    uselist=False,
    cascade="all, delete-orphan",
    passive_deletes=True,
)
