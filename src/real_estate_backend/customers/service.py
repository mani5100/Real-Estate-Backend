from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, select, func
from sqlalchemy.exc import IntegrityError
from real_estate_backend.core.exceptions import CustomerHasLeadsError, CustomerNotFoundError, EmailAlreadyExistsError
from real_estate_backend.customers.model import Customer
from real_estate_backend.customers.schema import CustomerCreate, CustomerUpdate, CustomerPaginatedResponse
from real_estate_backend.core.logging import log_call
from real_estate_backend.leads.model import Lead
from real_estate_backend.users.model import User
from real_estate_backend.core.exceptions import (
    CustomerProfileAlreadyExistsError,
    CustomerProfileNotFoundError,
)

@log_call
def get_all_customers(
    db: Session,
    *,
    search: str | None = None,
    is_active: bool | None = None,
    cursor: int | None = None,
    limit: int = 20,
) -> CustomerPaginatedResponse:
    base_filters = []

    if is_active is not None:
        base_filters.append(User.is_active == is_active)

    if search:
        normalized_search = search.strip()

        if normalized_search:
            pattern = f"%{normalized_search}%"

            base_filters.append(
                or_(
                    User.full_name.ilike(pattern),
                    User.email.ilike(pattern),
                    Customer.phone.ilike(pattern),
                )
            )

    page_filters = list(base_filters)

    if cursor is not None:
        page_filters.append(Customer.id > cursor)

    query = (
        select(Customer)
        .join(Customer.user)
        .options(joinedload(Customer.user))
        .where(*page_filters)
        .order_by(Customer.id.asc())
        .limit(limit + 1)
    )

    customers = list(db.scalars(query).unique().all())

    has_more = len(customers) > limit
    results = customers[:limit]

    next_cursor = (
        results[-1].id
        if has_more and results
        else None
    )

    total = db.scalar(
        select(func.count(Customer.id))
        .join(Customer.user)
        .where(*base_filters)
    ) or 0

    return CustomerPaginatedResponse(
        total=total,
        next_cursor=next_cursor,
        results=results,
    )
    
@log_call
def get_customer_by_id(
    db: Session,
    customer_id: int,
) -> Customer:
    customer = db.scalar(
        select(Customer)
        .options(joinedload(Customer.user))
        .where(Customer.id == customer_id)
    )

    if customer is None:
        raise CustomerNotFoundError(customer_id)

    return customer



@log_call
def delete_customer(db: Session, customer_id: int) -> None:
    customer = get_customer_by_id(db, customer_id)

    if customer.leads:
        raise CustomerHasLeadsError(customer_id)

    db.delete(customer)
    db.commit()
    
@log_call
def create_my_customer_profile(
    db: Session,
    current_user: User,
    data: CustomerCreate,
) -> Customer:
    existing_customer = db.scalar(
        select(Customer).where(
            Customer.user_id == current_user.id
        )
    )

    if existing_customer:
        raise CustomerProfileAlreadyExistsError()

    customer = Customer(
        user_id=current_user.id,
        phone=data.phone,
    )

    db.add(customer)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CustomerProfileAlreadyExistsError()

    db.refresh(customer)

    return db.scalar(
        select(Customer)
        .options(joinedload(Customer.user))
        .where(Customer.id == customer.id)
    )
    
@log_call
def get_my_customer_profile(
    db: Session,
    current_user: User,
) -> Customer:
    customer = db.scalar(
        select(Customer)
        .options(joinedload(Customer.user))
        .where(Customer.user_id == current_user.id)
    )

    if customer is None:
        raise CustomerProfileNotFoundError()

    return customer

@log_call
def update_my_customer_profile(
    db: Session,
    current_user: User,
    data: CustomerUpdate,
) -> Customer:
    customer = db.scalar(
        select(Customer)
        .options(joinedload(Customer.user))
        .where(Customer.user_id == current_user.id)
    )

    if customer is None:
        raise CustomerProfileNotFoundError()

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(customer, field, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(customer)

    return db.scalar(
        select(Customer)
        .options(joinedload(Customer.user))
        .where(Customer.id == customer.id)
    )
    
    
@log_call
def get_my_dashboard(
    db: Session,
    current_user: User,
) -> dict:
    customer = db.scalar(
        select(Customer)
        .options(
            joinedload(Customer.user),
            joinedload(Customer.leads).joinedload(Lead.property),
        )
        .where(Customer.user_id == current_user.id)
    )

    if customer is None:
        raise CustomerProfileNotFoundError()

    return {
        "id": customer.id,
        "user_id": customer.user_id,
        "phone": customer.phone,
        "full_name": customer.user.full_name,
        "email": customer.user.email,
        "leads": customer.leads,
    }