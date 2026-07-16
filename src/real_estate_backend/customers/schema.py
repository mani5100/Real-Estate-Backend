from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
import re


class CustomerBase(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    is_active: bool = True
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("full_name cannot be empty")
        if not re.match(r"^[A-Za-z\s]+$", v):
            raise ValueError("full_name must contain only letters and spaces")
        if len(v) < 2:
            raise ValueError("full_name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("full_name cannot exceed 100 characters")
        return v
    
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



class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    

class CustomerPaginatedResponse(BaseModel):
    total: int
    next_cursor: int | None
    results: list[CustomerResponse]