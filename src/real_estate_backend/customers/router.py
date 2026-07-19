from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from real_estate_backend.core.rate_limiter import rate_limiter
from real_estate_backend.core.database import get_db
from real_estate_backend.customers.schema import CustomerCreate, CustomerUpdate, CustomerResponse,CustomerPaginatedResponse
from real_estate_backend.customers import service
from real_estate_backend.auth.dependencies import get_current_user, require_admin, require_agent_or_admin
from real_estate_backend.users.model import User

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=CustomerPaginatedResponse)
def list_customers(
    is_active: bool | None = None,
    search: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    full_name: str | None = None,
    cursor: int | None = None,
    limit: int = 3,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    return service.get_all_customers(db, is_active, search, phone, email, full_name, cursor, limit)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    return service.get_customer_by_id(db, customer_id)


@router.post("/", response_model=CustomerResponse, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db),current_user: User = Depends(require_admin),
    _: None = Depends(rate_limiter)):
    return service.create_customer(db, data)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db),current_user: User = Depends(require_admin),
    _: None = Depends(rate_limiter)):
    return service.update_customer(db, customer_id, data)


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db),current_user: User = Depends(require_admin),
    _: None = Depends(rate_limiter)):
    service.delete_customer(db, customer_id)