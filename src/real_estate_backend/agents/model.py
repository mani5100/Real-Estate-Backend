from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from real_estate_backend.core.database import Base
from real_estate_backend.core.enums import AgentApplicationStatus

if TYPE_CHECKING:
    from real_estate_backend.users.model import User
    from real_estate_backend.properties.model import Property


class AgentProfile(Base):
    __tablename__ = "agent_profiles"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    license_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="agent_profile",
    )
    
    properties: Mapped[list[Property]] = relationship(
    "Property",
    back_populates="agent",
    cascade="all, delete-orphan",
    passive_deletes=True,
)
    
    
class AgentApplication(Base):
    __tablename__ = "agent_applications"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    status: Mapped[AgentApplicationStatus] = mapped_column(
        SAEnum(
            AgentApplicationStatus,
            name="agentapplicationstatus",
        ),
        nullable=False,
        default=AgentApplicationStatus.PENDING,
        server_default="PENDING",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped[User] = relationship(
        "User",
        back_populates="agent_application",
    )
    