from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from real_estate_backend.core.database import get_db
from real_estate_backend.leads.model import LeadStatus
from real_estate_backend.leads.schema import LeadCreate, LeadUpdate, LeadResponse, LeadDetailResponse
from real_estate_backend.leads import service

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("/", response_model=list[LeadResponse])
def list_leads(
    status: LeadStatus | None = None,
    agent_id: str | None = None,
    customer_id: int | None = None,
    property_id: int | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    return service.get_all_leads(db, status, agent_id, customer_id, property_id, search)


@router.get("/{lead_id}", response_model=LeadDetailResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    return service.get_lead_by_id(db, lead_id)


@router.post("/", response_model=LeadResponse, status_code=201)
def create_lead(data: LeadCreate, db: Session = Depends(get_db)):
    return service.create_lead(db, data)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db)):
    return service.update_lead(db, lead_id, data)


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: int, db: Session = Depends(get_db)):
    service.delete_lead(db, lead_id)