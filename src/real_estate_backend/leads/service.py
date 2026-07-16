from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from fastapi import HTTPException

from real_estate_backend.leads.model import Lead, LeadStatus
from real_estate_backend.leads.schema import LeadCreate, LeadUpdate


def get_all_leads(
    db: Session,
    status: LeadStatus | None,
    agent_id: str | None,
    customer_id: int | None,
    property_id: int | None,
    search: str | None,
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

    return db.scalars(stmt).all()


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
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead


def create_lead(db: Session, data: LeadCreate) -> Lead:
    lead = Lead(**data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead


def update_lead(db: Session, lead_id: int, data: LeadUpdate) -> Lead:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(lead, field, value)

    db.commit()
    db.refresh(lead)
    return lead


def delete_lead(db: Session, lead_id: int) -> None:
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    db.delete(lead)
    db.commit()