from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func
from real_estate_backend.core.exceptions import (
    LeadNotFoundError,
    CustomerNotFoundError,
    PropertyNotFoundError,
)
from real_estate_backend.leads.model import Lead, LeadStatus
from real_estate_backend.leads.schema import LeadCreate, LeadUpdate
from real_estate_backend.customers.model import Customer
from real_estate_backend.properties.model import Property
from real_estate_backend.core.logging import log_call

@log_call
def get_all_leads(
    db: Session,
    status: LeadStatus | None,
    agent_id: str | None,
    customer_id: int | None,
    property_id: int | None,
    search: str | None,
    cursor: int | None,
    limit: int
):
    stmt = select(Lead)

    if status:
        stmt = stmt.where(Lead.status == status)
    if agent_id:
        stmt = stmt.where(Lead.agent_id == agent_id)
    if customer_id:
        stmt = stmt.where(Lead.customer_id == customer_id)
    if property_id:
        stmt = stmt.where(Lead.property_id == property_id)
    if search:
        stmt = stmt.where(Lead.notes.ilike(f"%{search}%"))

    total = db.scalar(
    select(func.count()).select_from(stmt.subquery()))

    if cursor is not None:
        stmt = stmt.where(Lead.id > cursor)

    stmt = stmt.order_by(Lead.id).limit(limit)

    leads = db.scalars(stmt).all()

    next_cursor = leads[-1].id if len(leads) == limit else None

    return {
        "total": total,
        "next_cursor": next_cursor,
        "results": leads,
    }

@log_call
def get_lead_by_id(db: Session, lead_id: int) -> Lead:
    stmt = (
        select(Lead)
        .options(
            joinedload(Lead.customer),
            joinedload(Lead.property),
        )
        .where(Lead.id == lead_id)
    )
    lead = db.scalar(stmt)
    if not lead:
        raise LeadNotFoundError(lead_id)
    return lead

@log_call
def create_lead(db: Session, data: LeadCreate) -> Lead:
    
    customer = db.get(Customer, data.customer_id)
    if not customer:
        raise CustomerNotFoundError(data.customer_id)

    property = db.get(Property, data.property_id)
    if not property:
        raise PropertyNotFoundError(data.property_id)
    lead = Lead(**data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@log_call
def update_lead(db: Session, lead_id: int, data: LeadUpdate) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise LeadNotFoundError(lead_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)
    return lead

@log_call
def delete_lead(db: Session, lead_id: int) -> None:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise LeadNotFoundError(lead_id)

    db.delete(lead)
    db.commit()