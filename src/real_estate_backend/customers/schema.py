from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
import re


class CustomerBase(BaseModel):
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



class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    pass
    
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