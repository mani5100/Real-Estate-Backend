from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from real_estate_backend.agents.model import (
    AgentApplication,
    AgentProfile,
)
from real_estate_backend.core.enums import (
    AgentApplicationStatus,
    UserRole,
)
from real_estate_backend.agents.schema import AgentApplicationCreate, AgentApproveRequest, AgentPaginatedResponse, AgentProfileUpdate
from real_estate_backend.core.exceptions import (
    AgentAlreadyExistsError,
    AgentApplicationAlreadyExistsError,
    AgentApplicationInvalidStatusError,
    AgentApplicationNotFoundError,
    AgentLicenseAlreadyExistsError,
    AgentNotFoundError,
    AgentProfileNotFoundError,
)
from real_estate_backend.core.logging import log_call
from real_estate_backend.users.model import User


@log_call
def create_my_agent_application(
    db: Session,
    current_user: User,
    data: AgentApplicationCreate,
) -> AgentApplication:
    if current_user.role == UserRole.AGENT:
        raise AgentAlreadyExistsError()

    existing_profile = db.scalar(
        select(AgentProfile).where(
            AgentProfile.user_id == current_user.id
        )
    )

    if existing_profile is not None:
        raise AgentAlreadyExistsError()

    existing_application = db.scalar(
        select(AgentApplication).where(
            AgentApplication.user_id == current_user.id
        )
    )

    if existing_application is not None:
        raise AgentApplicationAlreadyExistsError()

    application = AgentApplication(
        user_id=current_user.id,
        status=AgentApplicationStatus.PENDING,
        license_number=data.license_number,
        phone=data.phone,
    )

    db.add(application)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AgentApplicationAlreadyExistsError()

    db.refresh(application)

    return application

@log_call
def get_my_agent_application(
    db: Session,
    current_user: User,
) -> AgentApplication:
    application = db.scalar(
        select(AgentApplication).where(
            AgentApplication.user_id == current_user.id
        )
    )

    if application is None:
        raise AgentApplicationNotFoundError()

    return application

@log_call
def get_all_agent_applications(
    db: Session,
) -> list[AgentApplication]:
    applications = db.scalars(
    select(AgentApplication)
    .options(joinedload(AgentApplication.user))
    .where(AgentApplication.status == AgentApplicationStatus.PENDING)
    .order_by(AgentApplication.created_at.desc())
).all()
    return [
    {
        "id": app.id,
        "user_id": app.user_id,
        "status": app.status.value,
        "created_at": app.created_at,
        "updated_at": app.updated_at,
        "user_full_name": app.user.full_name,
        "user_email": app.user.email,
    }
    for app in applications
]


@log_call
def approve_agent_application(
    db: Session,
    application_id: int,
) -> AgentProfile:
    application = db.scalar(
        select(AgentApplication)
        .options(joinedload(AgentApplication.user))
        .where(AgentApplication.id == application_id)
    )

    if application is None:
        raise AgentApplicationNotFoundError()

    if application.status != AgentApplicationStatus.PENDING:
        raise AgentApplicationInvalidStatusError()

    existing_profile = db.scalar(
        select(AgentProfile).where(
            AgentProfile.user_id == application.user_id
        )
    )

    if existing_profile is not None:
        raise AgentAlreadyExistsError()

    existing_license = db.scalar(
        select(AgentProfile).where(
            AgentProfile.license_number == application.license_number
        )
    )

    if existing_license is not None:
        raise AgentLicenseAlreadyExistsError()

    profile = AgentProfile(
        user_id=application.user_id,
        phone=application.phone,
        license_number=application.license_number,
    )

    application.status = AgentApplicationStatus.APPROVED
    application.user.role = UserRole.AGENT

    db.add(profile)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AgentLicenseAlreadyExistsError()

    db.refresh(profile)

    return db.scalar(
        select(AgentProfile)
        .options(joinedload(AgentProfile.user))
        .where(AgentProfile.id == profile.id)
    )


@log_call
def reject_agent_application(
    db: Session,
    application_id: int,
) -> AgentApplication:
    application = db.scalar(
        select(AgentApplication).where(
            AgentApplication.id == application_id
        )
    )

    if application is None:
        raise AgentApplicationNotFoundError()

    if application.status != AgentApplicationStatus.PENDING:
        raise AgentApplicationInvalidStatusError()

    application.status = AgentApplicationStatus.REJECTED

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(application)

    return application


@log_call
def get_my_agent_profile(
    db: Session,
    current_user: User,
) -> AgentProfile:
    profile = db.scalar(
        select(AgentProfile)
        .options(joinedload(AgentProfile.user))
        .where(AgentProfile.user_id == current_user.id)
    )

    if profile is None:
        raise AgentProfileNotFoundError()

    return profile


@log_call
def update_my_agent_profile(
    db: Session,
    current_user: User,
    data: AgentProfileUpdate,
) -> AgentProfile:
    profile = db.scalar(
        select(AgentProfile)
        .options(joinedload(AgentProfile.user))
        .where(AgentProfile.user_id == current_user.id)
    )

    if profile is None:
        raise AgentProfileNotFoundError()

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(profile)

    return db.scalar(
        select(AgentProfile)
        .options(joinedload(AgentProfile.user))
        .where(AgentProfile.id == profile.id)
    )
    
    
    
@log_call
def get_all_agents(
    db: Session,
    *,
    search: str | None = None,
    cursor: int | None = None,
    limit: int = 20,
) -> AgentPaginatedResponse:
    base_filters = []

    if search:
        normalized_search = search.strip()

        if normalized_search:
            pattern = f"%{normalized_search}%"

            base_filters.append(
                or_(
                    User.full_name.ilike(pattern),
                    User.email.ilike(pattern),
                    AgentProfile.phone.ilike(pattern),
                    AgentProfile.license_number.ilike(pattern),
                )
            )

    page_filters = list(base_filters)

    if cursor is not None:
        page_filters.append(AgentProfile.id > cursor)

    query = (
        select(AgentProfile)
        .join(AgentProfile.user)
        .options(joinedload(AgentProfile.user))
        .where(*page_filters)
        .order_by(AgentProfile.id.asc())
        .limit(limit + 1)
    )

    agents = list(db.scalars(query).unique().all())

    has_more = len(agents) > limit
    results = agents[:limit]

    next_cursor = (
        results[-1].id
        if has_more and results
        else None
    )

    total = db.scalar(
        select(func.count(AgentProfile.id))
        .join(AgentProfile.user)
        .where(*base_filters)
    ) or 0

    return AgentPaginatedResponse(
        total=total,
        next_cursor=next_cursor,
        results=results,
    )


@log_call
def get_agent_by_id(
    db: Session,
    agent_id: int,
) -> AgentProfile:
    profile = db.scalar(
        select(AgentProfile)
        .options(joinedload(AgentProfile.user))
        .where(AgentProfile.id == agent_id)
    )

    if profile is None:
        raise AgentNotFoundError(agent_id)

    return profile