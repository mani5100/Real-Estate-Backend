from sqlalchemy.orm import Session
from sqlalchemy import select,func
from fastapi import HTTPException

from real_estate_backend.properties.model import Property
from real_estate_backend.properties.schema import PropertyCreate, PropertyUpdate


def get_all_properties(
    db: Session,
    city: str | None,
    min_price: float | None,
    max_price: float | None,
    min_bedrooms: int | None,
    is_available: bool | None,
):
    stmt = select(Property)

    if city:
        stmt = stmt.where(Property.city.ilike(f"%{city}%"))
    if min_price is not None:
        stmt = stmt.where(Property.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Property.price <= max_price)
    if min_bedrooms is not None:
        stmt = stmt.where(Property.bedrooms >= min_bedrooms)
    if is_available is not None:
        stmt = stmt.where(Property.is_available == is_available)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    properties = db.scalars(stmt).all()

    return {"total": total, "results": properties}


def get_property_by_id(db: Session, property_id: int) -> Property:
    prop = db.get(Property, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


def create_property(db: Session, data: PropertyCreate) -> Property:
    prop = Property(**data.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


def update_property(db: Session, property_id: int, data: PropertyUpdate) -> Property:
    prop = get_property_by_id(db, property_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prop, field, value)

    db.commit()
    db.refresh(prop)
    return prop


def delete_property(db: Session, property_id: int) -> None:
    prop = get_property_by_id(db, property_id)

    if prop.leads:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete property with existing leads"
        )

    db.delete(prop)
    db.commit()
    
    
def get_properties_by_bedrooms(db: Session, bedrooms: int) -> list[Property]:
    stmt = select(Property).where(Property.bedrooms == bedrooms)
    properties = db.scalars(stmt).all()
    if not properties:
        raise HTTPException(status_code=404, detail=f"No properties found with {bedrooms} bedrooms")
    return properties