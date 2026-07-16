from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class PropertyBase(BaseModel):
    title: str
    city: str
    address: str
    price: float
    bedrooms: int = 1
    bathrooms: int = 1
    area_sqft: Optional[float] = None
    description: Optional[str] = None
    is_available: bool = True


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    price: Optional[float] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[float] = None
    description: Optional[str] = None
    is_available: Optional[bool] = None


class PropertyResponse(PropertyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
    
class PropertyListResponse(BaseModel):
    total: int
    next_cursor: int | None
    results: list[PropertyResponse]
    
