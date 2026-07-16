from sqlalchemy.orm import Session
from sqlalchemy import select,func
from real_estate_backend.core.exceptions import (
    PropertyNotFoundError,
    PropertyHasLeadsError,
    NoPropertiesFoundError
)
from real_estate_backend.properties.model import Property
from real_estate_backend.properties.schema import PropertyCreate, PropertyUpdate
from real_estate_backend.core.logging import log_call

@log_call
def get_all_properties(
    db: Session,
    city: str | None,
    min_price: float | None,
    max_price: float | None,
    min_bedrooms: int | None,
    is_available: bool | None,
    cursor: int | None,
    limit: int
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
    if cursor is not None:
        stmt = stmt.where(Property.id > cursor)
        
    stmt = stmt.order_by(Property.id).limit(limit)
    properties = db.scalars(stmt).all()
    
    next_cursor = properties[-1].id if len(properties) == limit else None
    
    return {
        "total": total,
        "next_cursor": next_cursor,
        "results": properties,
    }

@log_call
def get_property_by_id(db: Session, property_id: int) -> Property:
    prop = db.get(Property, property_id)
    if not prop:
        raise PropertyNotFoundError(property_id)
    return prop

@log_call
def create_property(db: Session, data: PropertyCreate) -> Property:
    prop = Property(**data.model_dump())
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop

@log_call
def update_property(db: Session, property_id: int, data: PropertyUpdate) -> Property:
    prop = get_property_by_id(db, property_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(prop, field, value)

    db.commit()
    db.refresh(prop)
    return prop

@log_call
def delete_property(db: Session, property_id: int) -> None:
    prop = get_property_by_id(db, property_id)

    if prop.leads:
         raise PropertyHasLeadsError(property_id)

    db.delete(prop)
    db.commit()
    
@log_call   
def get_properties_by_bedrooms(db: Session, bedrooms: int) -> list[Property]:
    stmt = select(Property).where(Property.bedrooms == bedrooms)
    properties = db.scalars(stmt).all()
    if not properties:
        raise NoPropertiesFoundError(bedrooms)
    return properties