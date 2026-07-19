import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from real_estate_backend.main import app
from real_estate_backend.core.database import Base, get_db
from real_estate_backend.core.enums import UserRole
from real_estate_backend.core.security import hash_password, create_access_token
from real_estate_backend.users.model import User
from real_estate_backend.customers.model import Customer
from real_estate_backend.properties.model import Property
from real_estate_backend.leads.model import Lead, LeadStatus
from real_estate_backend.core.rate_limiter import rate_limiter
from real_estate_backend.core.rate_limit_store import rate_limit_store

# ── SQLite in-memory engine ────────────────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # same connection across threads
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ── DB fixture — fresh tables per test ────────────────────────
@pytest.fixture()
def db():
    """
    Creates all tables before each test.
    Drops all tables after each test.
    Every test gets a completely clean database.
    """
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ── Client fixture — overrides DB dependency ──────────────────
@pytest.fixture()
def client(db):
    """
    Creates TestClient with DB override.
    Every request in tests hits SQLite not Postgres.
    """
    def override_get_db():
        try:
            db.expire_all()
            yield db
        finally:
            pass  # db fixture handles closing

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── Helper — create user directly in DB ───────────────────────
def create_user(db, email: str, role: UserRole, full_name: str = "Test User") -> User:
    """Creates a user directly in DB — bypasses HTTP layer."""
    user = User(
        email=email,
        password=hash_password("Test1234"),
        full_name=full_name,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_token(user: User) -> str:
    """Generates a real JWT token for a user."""
    return create_access_token({
        "user_id": user.id,
        "role": user.role.value,
    })


# ── Role fixtures ─────────────────────────────────────────────
@pytest.fixture()
def admin_user(db):
    return create_user(db, "admin@test.com", UserRole.ADMIN, "Admin User")


@pytest.fixture()
def agent_user(db):
    return create_user(db, "agent@test.com", UserRole.AGENT, "Agent User")


@pytest.fixture()
def customer_user(db):
    return create_user(db, "customer@test.com", UserRole.CUSTOMER, "Customer User")


@pytest.fixture()
def admin_token(admin_user):
    return get_token(admin_user)


@pytest.fixture()
def agent_token(agent_user):
    return get_token(agent_user)


@pytest.fixture()
def customer_token(customer_user):
    return get_token(customer_user)


# ── Auth headers helper ───────────────────────────────────────
def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Seed helpers — create domain objects directly in DB ───────
def make_customer(db, email: str = "john@test.com") -> Customer:
    customer = Customer(
        full_name="John Doe",
        email=email,
        phone="03001234567",
        is_active=True,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def make_property(db) -> Property:
    prop = Property(
        title="Modern Apartment",
        city="Lahore",
        address="12 Gulberg Street",
        price=5000000,
        bedrooms=3,
        bathrooms=2,
        area_sqft=1200,
        is_available=True,
    )
    db.add(prop)
    db.commit()
    db.refresh(prop)
    return prop


def make_lead(db, customer_id: int, property_id: int, agent_id: int) -> Lead:
    lead = Lead(
        customer_id=customer_id,
        property_id=property_id,
        agent_id=agent_id,
        status=LeadStatus.NEW,
        notes="Test lead",
    )
    db.add(lead)
    db.flush()
    db.refresh(lead)
    return lead


@pytest.fixture(autouse=True)
def reset_rate_limit_store():
    """
    Clears rate limit store before every test.
    autouse=True means it runs automatically — no need to add to each test.
    """
    rate_limit_store._store.clear()
    yield
    rate_limit_store._store.clear()