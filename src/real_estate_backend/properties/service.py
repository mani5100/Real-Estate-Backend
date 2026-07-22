from sqlalchemy import func, select
from sqlalchemy.orm import Session

from real_estate_backend.agents.model import AgentProfile
from real_estate_backend.core.enums import UserRole
from real_estate_backend.core.exceptions import (
    AgentProfileNotFoundError,
    NoPropertiesFoundError,
    PermissionDeniedError,
    PropertyHasLeadsError,
    PropertyNotFoundError,
)
from real_estate_backend.core.logging import log_call
from real_estate_backend.properties.model import Property
from real_estate_backend.properties.schema import (
    PropertyCreate,
    PropertyUpdate,
)
from real_estate_backend.users.model import User


def _get_agent_profile(
    db: Session,
    current_user: User,
) -> AgentProfile:
    profile = db.scalar(
        select(AgentProfile).where(
            AgentProfile.user_id == current_user.id
        )
    )

    if profile is None:
        raise AgentProfileNotFoundError()

    return profile


def _check_property_management_permission(
    db: Session,
    current_user: User,
    property_record: Property,
) -> None:
    if current_user.role == UserRole.ADMIN:
        return

    agent_profile = _get_agent_profile(
        db=db,
        current_user=current_user,
    )

    if property_record.agent_id != agent_profile.id:
        raise PermissionDeniedError(
            "you can only manage your own properties"
        )


@log_call
def get_all_properties(
    db: Session,
    city: str | None,
    min_price: float | None,
    max_price: float | None,
    min_bedrooms: int | None,
    is_available: bool | None,
    cursor: int | None,
    limit: int,
):
    stmt = select(Property)

    if city:
        stmt = stmt.where(
            Property.city.ilike(f"%{city.strip()}%")
        )

    if min_price is not None:
        stmt = stmt.where(Property.price >= min_price)

    if max_price is not None:
        stmt = stmt.where(Property.price <= max_price)

    if min_bedrooms is not None:
        stmt = stmt.where(
            Property.bedrooms >= min_bedrooms
        )

    if is_available is not None:
        stmt = stmt.where(
            Property.is_available == is_available
        )

    total = db.scalar(
        select(func.count()).select_from(stmt.subquery())
    ) or 0

    if cursor is not None:
        stmt = stmt.where(Property.id > cursor)

    stmt = (
        stmt
        .order_by(Property.id.asc())
        .limit(limit + 1)
    )

    properties = list(db.scalars(stmt).all())

    has_more = len(properties) > limit
    results = properties[:limit]

    next_cursor = (
        results[-1].id
        if has_more and results
        else None
    )

    return {
        "total": total,
        "next_cursor": next_cursor,
        "results": results,
    }


@log_call
def get_property_by_id(
    db: Session,
    property_id: int,
) -> Property:
    property_record = db.get(Property, property_id)

    if property_record is None:
        raise PropertyNotFoundError(property_id)

    return property_record


@log_call
def create_property(
    db: Session,
    data: PropertyCreate,
    current_user: User,
) -> Property:
    agent_profile = _get_agent_profile(
        db=db,
        current_user=current_user,
    )

    property_record = Property(
        **data.model_dump(),
        agent_id=agent_profile.id,
    )

    db.add(property_record)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(property_record)
    return property_record


@log_call
def update_property(
    db: Session,
    property_id: int,
    data: PropertyUpdate,
    current_user: User,
) -> Property:
    property_record = get_property_by_id(
        db=db,
        property_id=property_id,
    )

    _check_property_management_permission(
        db=db,
        current_user=current_user,
        property_record=property_record,
    )

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(property_record, field, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(property_record)
    return property_record


@log_call
def delete_property(
    db: Session,
    property_id: int,
    current_user: User,
) -> None:
    property_record = get_property_by_id(
        db=db,
        property_id=property_id,
    )

    _check_property_management_permission(
        db=db,
        current_user=current_user,
        property_record=property_record,
    )

    if property_record.leads:
        raise PropertyHasLeadsError(property_id)

    db.delete(property_record)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


@log_call
def get_properties_by_bedrooms(
    db: Session,
    bedrooms: int,
) -> list[Property]:
    properties = list(
        db.scalars(
            select(Property).where(
                Property.bedrooms == bedrooms
            )
        ).all()
    )

    if not properties:
        raise NoPropertiesFoundError(bedrooms)

    return properties