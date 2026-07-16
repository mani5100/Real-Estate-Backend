from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Any
from real_estate_backend.core.database import get_db
from real_estate_backend.properties.schema import PropertyCreate, PropertyUpdate, PropertyResponse, PropertyListResponse
from real_estate_backend.properties import service

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.get("/", response_model=PropertyListResponse)
def list_properties(
    city: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_bedrooms: int | None = None,
    is_available: bool | None = None,
    cursor: int | None = None,
    limit: int = 3,
    db: Session = Depends(get_db),
):
    return service.get_all_properties(db, city, min_price, max_price, min_bedrooms, is_available,cursor,limit)

@router.get("/bedrooms/{bedrooms}", response_model=list[PropertyResponse])
def get_properties_by_bedrooms(bedrooms: int, db: Session = Depends(get_db)):
    return service.get_properties_by_bedrooms(db, bedrooms)

@router.get("/{property_id}", response_model=PropertyResponse)
def get_property(property_id: int, db: Session = Depends(get_db)):
    return service.get_property_by_id(db, property_id)


@router.post("/", response_model=PropertyResponse, status_code=201)
def create_property(data: PropertyCreate, db: Session = Depends(get_db)):
    return service.create_property(db, data)


@router.patch("/{property_id}", response_model=PropertyResponse)
def update_property(property_id: int, data: PropertyUpdate, db: Session = Depends(get_db)):
    return service.update_property(db, property_id, data)


@router.delete("/{property_id}", status_code=204)
def delete_property(property_id: int, db: Session = Depends(get_db)):
    service.delete_property(db, property_id)
