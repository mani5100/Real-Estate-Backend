from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from real_estate_backend.core.exceptions import CustomerHasLeadsError, CustomerNotFoundError
from real_estate_backend.core.rate_limiter import rate_limiter
from real_estate_backend.core.database import get_db
from real_estate_backend.customers.model import Customer
from real_estate_backend.customers.schema import CustomerCreate, CustomerDashboardResponse, CustomerUpdate, CustomerResponse,CustomerPaginatedResponse
from real_estate_backend.customers import service
from real_estate_backend.auth.dependencies import get_current_user, require_admin, require_agent_or_admin
from real_estate_backend.users.model import User

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post(
    "/me",
    response_model=CustomerResponse,
    status_code=201,
)
def create_my_customer_profile(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(rate_limiter),
):
    return service.create_my_customer_profile(
        db=db,
        current_user=current_user,
        data=data,
    )

@router.get(
    "/me",
    response_model=CustomerResponse,
    status_code=200,
)
def get_my_customer_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_my_customer_profile(
        db=db,
        current_user=current_user,
    )
    
@router.patch(
    "/me",
    response_model=CustomerResponse,
    status_code=200,
)
def update_my_customer_profile(
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(rate_limiter),
):
    return service.update_my_customer_profile(
        db=db,
        current_user=current_user,
        data=data,
    )

@router.get(
    "/",
    response_model=CustomerPaginatedResponse,
)
def get_all_customers(
    search: str | None = None,
    is_active: bool | None = None,
    cursor: int | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return service.get_all_customers(
        db=db,
        search=search,
        is_active=is_active,
        cursor=cursor,
        limit=limit,
    )
  
@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return service.get_customer_by_id(db, customer_id)

@router.delete(
    "/{customer_id}",
    status_code=204,
)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _: None = Depends(rate_limiter),
) -> Response:
    service.delete_customer(
        db=db,
        customer_id=customer_id,
    )

    return Response(status_code=204)
    
@router.get(
    "/me/interests",
    response_model=CustomerDashboardResponse,
    status_code=200,
)
def get_my_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_my_dashboard(
        db=db,
        current_user=current_user,
    )