from sqlalchemy.orm import Session
from sqlalchemy import select, func
from fastapi import HTTPException

from real_estate_backend.customers.model import Customer
from real_estate_backend.customers.schema import CustomerCreate, CustomerUpdate


def get_all_customers(
    db: Session,
    is_active: bool | None,
    search: str | None,
    phone: str | None,
    email: str | None,
    full_name: str | None,
    cursor: int | None,
    limit: int,
    
):
    stmt = select(Customer)

    if is_active is not None:
        stmt = stmt.where(Customer.is_active == is_active)
    if search:
        stmt = stmt.where(Customer.full_name.ilike(f"%{search}%"))
    if phone:
        stmt = stmt.where(Customer.phone == phone)
    if email:
        stmt = stmt.where(Customer.email.ilike(f"%{email}%"))
    if full_name:
        stmt = stmt.where(Customer.full_name.ilike(f"%{full_name}%"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    
    if cursor:
        stmt = stmt.where(Customer.id > cursor)

    stmt = stmt.order_by(Customer.id).limit(limit)

    customers = db.scalars(stmt).all()

    next_cursor = customers[-1].id if len(customers) == limit else None

    return {"total": total, "next_cursor": next_cursor, "results": customers}


def get_customer_by_id(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


def create_customer(db: Session, data: CustomerCreate) -> Customer:
    existing = db.scalar(select(Customer).where(Customer.email == data.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(db: Session, customer_id: int, data: CustomerUpdate) -> Customer:
    customer = get_customer_by_id(db, customer_id)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer


def delete_customer(db: Session, customer_id: int) -> None:
    customer = get_customer_by_id(db, customer_id)

    if customer.leads:
        raise HTTPException(
            status_code=409,
            detail="Cannot delete customer with existing leads"
        )

    db.delete(customer)
    db.commit()