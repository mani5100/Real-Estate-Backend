from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from real_estate_backend.agents import service
from real_estate_backend.agents.schema import (
    AgentApplicationCreate,
    AgentApplicationListResponse,
    AgentApplicationResponse,
    AgentApproveRequest,
    AgentPaginatedResponse,
    AgentProfileResponse,
    AgentProfileUpdate,
)
from real_estate_backend.auth.dependencies import get_current_user, require_admin, require_agent
from real_estate_backend.core.database import get_db
from real_estate_backend.core.rate_limiter import rate_limiter
from real_estate_backend.users.model import User


router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)

@router.get(
    "/me",
    response_model=AgentProfileResponse,
    status_code=status.HTTP_200_OK,
)
def get_my_agent_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent),
):
    return service.get_my_agent_profile(
        db=db,
        current_user=current_user,
    )
    
@router.patch(
    "/me",
    response_model=AgentProfileResponse,
    status_code=status.HTTP_200_OK,
)
def update_my_agent_profile(
    data: AgentProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_agent),
    _: None = Depends(rate_limiter),
):
    return service.update_my_agent_profile(
        db=db,
        current_user=current_user,
        data=data,
    )
    
    

@router.post(
    "/applications/me",
    response_model=AgentApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_my_agent_application(
    data: AgentApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(rate_limiter),
):
    return service.create_my_agent_application(
        db=db,
        current_user=current_user,
        data=data,
    )


@router.get(
    "/",
    response_model=AgentPaginatedResponse,
    status_code=status.HTTP_200_OK,
)
def get_all_agents(
    search: str | None = None,
    cursor: int | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return service.get_all_agents(
        db=db,
        search=search,
        cursor=cursor,
        limit=limit,
    )




@router.get(
    "/applications/me",
    response_model=AgentApplicationResponse,
    status_code=status.HTTP_200_OK,
)
def get_my_agent_application(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_my_agent_application(
        db=db,
        current_user=current_user,
    )
    
    
@router.get(
    "/applications",
    response_model=AgentApplicationListResponse,
    status_code=status.HTTP_200_OK,
)
def get_all_agent_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    applications = service.get_all_agent_applications(db=db)

    return AgentApplicationListResponse(
        results=applications,
    )


@router.post(
    "/applications/{application_id}/approve",
    response_model=AgentProfileResponse,
    status_code=status.HTTP_200_OK,
)
def approve_agent_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _: None = Depends(rate_limiter),
):
    return service.approve_agent_application(
        db=db,
        application_id=application_id
    )

@router.get(
    "/{agent_id}",
    response_model=AgentProfileResponse,
    status_code=status.HTTP_200_OK,
)
def get_agent_by_id(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return service.get_agent_by_id(
        db=db,
        agent_id=agent_id,
    )

@router.post(
    "/applications/{application_id}/reject",
    response_model=AgentApplicationResponse,
    status_code=status.HTTP_200_OK,
)
def reject_agent_application(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    _: None = Depends(rate_limiter),
):
    return service.reject_agent_application(
        db=db,
        application_id=application_id,
    )
    
