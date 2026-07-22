from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from real_estate_backend.core.database import Base, get_db
from real_estate_backend.core.enums import UserRole
from real_estate_backend.core.rate_limit_store import rate_limit_store
from real_estate_backend.core.security import (
    create_access_token,
    hash_password,
)
from real_estate_backend.customers.model import Customer
from real_estate_backend.agents.model import AgentProfile
from real_estate_backend.leads.model import Lead, LeadStatus
from real_estate_backend.properties.model import Property
from real_estate_backend.users.model import User
from real_estate_backend.main import app
from real_estate_backend.agents.model import (
    AgentApplication,
    AgentProfile,
)

# ---------------------------------------------------------------------------
# Test database
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for every test.

    SQLite is used for speed. StaticPool ensures the same in-memory
    connection is available to both the test and FastAPI's TestClient.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db: Session) -> Session:
    """
    Alias for tests that use the name `db_session`.

    Existing tests can continue using `db`, while newer tests can use
    `db_session`.
    """
    return db


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Override the application's database dependency so API requests use
    the same test database session.
    """

    def override_get_db() -> Generator[Session, None, None]:
        db.expire_all()
        yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Authentication helpers
# ---------------------------------------------------------------------------


def create_user(
    db: Session,
    email: str,
    role: UserRole,
    full_name: str = "Test User",
    password: str = "Test1234",
    is_active: bool = True,
) -> User:
    """Create a user directly in the test database."""
    user = User(
        email=email.lower(),
        password=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=is_active,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_token(user: User) -> str:
    """Generate a real JWT token matching get_current_user()."""
    return create_access_token(
        {
            "user_id": user.id,
            "role": user.role.value,
        }
    )


def auth_headers(token: str) -> dict[str, str]:
    """Build an Authorization header for an access token."""
    return {
        "Authorization": f"Bearer {token}",
    }


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def normal_user(db: Session) -> User:
    return create_user(
        db=db,
        email="user@test.com",
        role=UserRole.USER,
        full_name="Normal User",
    )


@pytest.fixture()
def admin_user(db: Session) -> User:
    return create_user(
        db=db,
        email="admin@test.com",
        role=UserRole.ADMIN,
        full_name="Admin User",
    )


@pytest.fixture()
def agent_user(db: Session) -> User:
    return create_user(
        db=db,
        email="agent@test.com",
        role=UserRole.AGENT,
        full_name="Agent User",
    )


@pytest.fixture()
def user_token(normal_user: User) -> str:
    return get_token(normal_user)


@pytest.fixture()
def admin_token(admin_user: User) -> str:
    return get_token(admin_user)


@pytest.fixture()
def agent_token(agent_user: User) -> str:
    return get_token(agent_user)


@pytest.fixture()
def user_headers(user_token: str) -> dict[str, str]:
    return auth_headers(user_token)


@pytest.fixture()
def admin_headers(admin_token: str) -> dict[str, str]:
    return auth_headers(admin_token)


@pytest.fixture()
def agent_headers(agent_token: str) -> dict[str, str]:
    return auth_headers(agent_token)


# ---------------------------------------------------------------------------
# Temporary compatibility fixtures
# ---------------------------------------------------------------------------
#
# Some older property and lead tests still use "customer_user" and
# "customer_token". Authentication no longer has a CUSTOMER role, so these
# aliases now represent a normal USER.
#
# Remove these aliases after the remaining test files have been renamed.


@pytest.fixture()
def customer_user(normal_user: User) -> User:
    return normal_user


@pytest.fixture()
def customer_token(user_token: str) -> str:
    return user_token


@pytest.fixture()
def customer_headers(user_headers: dict[str, str]) -> dict[str, str]:
    return user_headers


# ---------------------------------------------------------------------------
# Domain-object helpers
# ---------------------------------------------------------------------------


def make_customer(
    db: Session,
    email: str = "john@test.com",
    full_name: str = "John Doe",
    phone: str | None = "03001234567",
    user: User | None = None,
) -> Customer:
    """
    Create a customer profile linked to a USER account.

    Customer account data such as email and full_name belongs to User.
    """
    if user is None:
        existing_user = db.scalar(
            select(User).where(User.email == email.lower())
        )

        if existing_user is not None:
            user = existing_user
        else:
            user = create_user(
                db=db,
                email=email,
                role=UserRole.USER,
                full_name=full_name,
            )

    existing_customer = db.scalar(
        select(Customer).where(Customer.user_id == user.id)
    )

    if existing_customer is not None:
        return existing_customer

    customer = Customer(
        user_id=user.id,
        phone=phone,
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer

def get_or_create_agent_profile(
    db: Session,
    agent: User,
) -> AgentProfile:
    profile = db.scalar(
        select(AgentProfile).where(
            AgentProfile.user_id == agent.id
        )
    )

    if profile is not None:
        return profile

    profile = AgentProfile(
        user_id=agent.id,
        phone=None,
        license_number=f"TEST-LIC-{agent.id}",
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile

def make_property(
    db: Session,
    *,
    agent: User | None = None,
    title: str = "Modern Apartment",
    city: str = "Lahore",
    address: str | None = None,
    price: int = 5_000_000,
    bedrooms: int = 3,
    bathrooms: int = 2,
    area_sqft: float = 1200,
    is_available: bool = True,
) -> Property:
    """
    Create a property with a valid agent owner.

    The current Property model requires agent_id.
    """
    if agent is None:
        agent_count = db.scalar(
            select(func.count(User.id)).where(
                User.role == UserRole.AGENT
            )
        ) or 0

        agent = create_user(
            db=db,
            email=f"property-agent-{agent_count + 1}@test.com",
            role=UserRole.AGENT,
            full_name=f"Property Agent {agent_count + 1}",
        )

    property_count = db.scalar(
        select(func.count(Property.id))
    ) or 0

    if address is None:
        address = f"{property_count + 1} Gulberg Street"

    agent_profile = get_or_create_agent_profile(
    db=db,
    agent=agent,
)

    prop = Property(
        agent_id=agent_profile.id,
        title=title,
        city=city,
        address=address,
        price=price,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        area_sqft=area_sqft,
        is_available=is_available,
    )

    db.add(prop)
    db.commit()
    db.refresh(prop)

    return prop


def make_lead(
    db: Session,
    customer_id: int,
    property_id: int,
    agent_id: int | None,
    status: LeadStatus = LeadStatus.NEW,
    notes: str | None = "Test lead",
) -> Lead:
    """Create a lead directly in the test database."""
    lead = Lead(
        customer_id=customer_id,
        property_id=property_id,
        agent_id=agent_id,
        status=status,
        notes=notes,
    )

    db.add(lead)
    db.commit()
    db.refresh(lead)

    return lead


# ---------------------------------------------------------------------------
# Reusable domain fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def customer_profile(
    db: Session,
    normal_user: User,
) -> Customer:
    return make_customer(
        db=db,
        user=normal_user,
        phone="+923001234567",
    )


@pytest.fixture()
def property_record(
    db: Session,
    agent_user: User,
) -> Property:
    return make_property(
        db=db,
        agent=agent_user,
    )


@pytest.fixture()
def lead_record(
    db: Session,
    customer_profile: Customer,
    property_record: Property,
    agent_user: User,
) -> Lead:
    return make_lead(
        db=db,
        customer_id=customer_profile.id,
        property_id=property_record.id,
        agent_id=agent_user.id,
    )

@pytest.fixture()
def agent_profile(
    db: Session,
    agent_user: User,
) -> AgentProfile:
    return get_or_create_agent_profile(
        db=db,
        agent=agent_user,
    )

# ---------------------------------------------------------------------------
# Automatic cleanup
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_rate_limit_store():
    """Clear in-memory rate-limit state before and after every test."""
    rate_limit_store._store.clear()

    yield

    rate_limit_store._store.clear()