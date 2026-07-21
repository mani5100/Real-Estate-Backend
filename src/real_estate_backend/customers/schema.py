from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
import re


class CustomerBase(BaseModel):
    phone: Optional[str] = None
    model_config = ConfigDict(extra="forbid")
    

    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        # Allows: 03001234567, +923001234567, 0300-1234567
        if not re.match(r"^\+?[\d\s\-]{7,20}$", v):
            raise ValueError("phone must contain only digits, spaces, hyphens, or + prefix")
        return v



class CustomerCreate(BaseModel):
    phone: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not re.fullmatch(r"\+?[\d\s\-]{7,20}", value):
            raise ValueError(
                "phone must contain only digits, spaces, hyphens, "
                "or a leading +"
            )

        return value


class CustomerUpdate(BaseModel):
    phone: str | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not re.fullmatch(r"\+?[\d\s\-]{7,20}", value):
            raise ValueError(
                "phone must contain only digits, spaces, hyphens, "
                "or a leading +"
            )

        return value
    
class CustomerUserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
    
class CustomerResponse(BaseModel):
    id: int
    user_id: int
    phone: str | None
    created_at: datetime
    updated_at: datetime
    user: CustomerUserResponse

    model_config = ConfigDict(from_attributes=True)
    

class CustomerPaginatedResponse(BaseModel):
    total: int
    next_cursor: int | None
    results: list[CustomerResponse]