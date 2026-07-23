from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import datetime
from typing import Optional
from real_estate_backend.core.enums import PropertyType
from real_estate_backend.core.enums import PaymentMethod


class PropertyBase(BaseModel):
    title: str
    city: str
    address: str
    price: int = Field(gt=0)
    bedrooms: int = Field(default=1, ge=0)
    bathrooms: int = Field(default=1, ge=0)
    area_sqft: Optional[float] = None
    description: Optional[str] = None
    is_available: bool = True
    property_type: Optional[PropertyType] = None
    model_config = ConfigDict(extra="forbid")
    
    @field_validator("city")
    @classmethod
    def validate_city(cls, city: str) -> str:
        city = city.strip()

        if not city.replace(" ", "").isalpha():
            raise ValueError("City must contain only letters and spaces")

        return city


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    price: Optional[int] = Field(default=None, gt=0)
    bedrooms: Optional[int] = Field(default=None, ge=0)
    bathrooms: Optional[int] = Field(default=None, ge=0)
    area_sqft: Optional[float] = Field(default=None, gt=0)
    description: Optional[str] = None
    is_available: Optional[bool] = None
    property_type: Optional[PropertyType] = None
    
    @field_validator("city")
    @classmethod
    def validate_city(cls, city: Optional[str]) -> Optional[str]:
        if city is None:
            return None

        city = city.strip()

        if not city.replace(" ", "").isalpha():
            raise ValueError("City must contain only letters and spaces")

        return city


class PropertyResponse(PropertyBase):
    id: int
    agent_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class PropertyListResponse(BaseModel):
    total: int
    next_cursor: int | None
    results: list[PropertyResponse]
    
