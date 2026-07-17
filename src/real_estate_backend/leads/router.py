from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from real_estate_backend.core.database import get_db
from real_estate_backend.leads.model import LeadStatus
from real_estate_backend.leads.schema import LeadCreate, LeadUpdate, LeadResponse, LeadDetailResponse, LeadPaginatedResponse
from real_estate_backend.leads import service
from real_estate_backend.auth.dependencies import get_current_user
from real_estate_backend.users.model import User

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.get("/", response_model=LeadPaginatedResponse)
def list_leads(
    status: LeadStatus | None = None,
    agent_id: str | None = None,
    customer_id: int | None = None,
    property_id: int | None = None,
    search: str | None = None,
    cursor: int | None = None,
    limit: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_all_leads(db, status, agent_id, customer_id, property_id, search, cursor, limit)


@router.get("/{lead_id}", response_model=LeadDetailResponse)
def get_lead(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):
    return service.get_lead_by_id(db, lead_id)


@router.post("/", response_model=LeadResponse, status_code=201)
def create_lead(data: LeadCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):
    return service.create_lead(db, data)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: int, data: LeadUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):
    return service.update_lead(db, lead_id, data)


@router.delete("/{lead_id}", status_code=204)
def delete_lead(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),):
    service.delete_lead(db, lead_id)