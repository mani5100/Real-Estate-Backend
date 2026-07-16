from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from real_estate_backend.core.database import get_db
from real_estate_backend.customers.schema import CustomerCreate, CustomerUpdate, CustomerResponse
from real_estate_backend.customers import service

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=list[CustomerResponse])
def list_customers(
    is_active: bool | None = None,
    search: str | None = None,
    phone: str | None = None,
    email: str | None = None,
    full_name: str | None = None,
    db: Session = Depends(get_db),
):
    return service.get_all_customers(db, is_active, search, phone, email, full_name)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    return service.get_customer_by_id(db, customer_id)


@router.post("/", response_model=CustomerResponse, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    return service.create_customer(db, data)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db)):
    return service.update_customer(db, customer_id, data)


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    service.delete_customer(db, customer_id)