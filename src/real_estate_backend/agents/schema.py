import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from real_estate_backend.core.enums import AgentApplicationStatus



class AgentApplicationResponse(BaseModel):
    id: int
    user_id: int
    status: AgentApplicationStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AgentApplicationListResponse(BaseModel):
    results: list[AgentApplicationResponse]

class AgentApproveRequest(BaseModel):
    phone: str | None = None
    license_number: str

    model_config = ConfigDict(extra="forbid")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if not re.fullmatch(r"\+?[\d\s\-]{7,20}", value):
            raise ValueError(
                "phone must contain only digits, spaces, hyphens, "
                "or a leading +"
            )

        return value

    @field_validator("license_number")
    @classmethod
    def validate_license_number(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("license_number cannot be empty")

        if len(value) > 50:
            raise ValueError(
                "license_number cannot exceed 50 characters"
            )

        return value


class AgentProfileUpdate(BaseModel):
    phone: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if not re.fullmatch(r"\+?[\d\s\-]{7,20}", value):
            raise ValueError(
                "phone must contain only digits, spaces, hyphens, "
                "or a leading +"
            )

        return value


class AgentUserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class AgentProfileResponse(BaseModel):
    id: int
    user_id: int
    phone: str | None
    license_number: str
    created_at: datetime
    updated_at: datetime
    user: AgentUserResponse

    model_config = ConfigDict(from_attributes=True)
    
    
class AgentPaginatedResponse(BaseModel):
    total: int
    next_cursor: int | None
    results: list[AgentProfileResponse]