import pytest
from tests.conftest import make_customer, make_property, make_lead, auth_headers


# ── Happy Path ─────────────────────────────────────────────────

def test_create_customer_happy_path(client, db, admin_token):
    """Admin creates customer → 201 with correct data returned."""
    response = client.post(
        "/customers/",
        json={
            "full_name": "John Doe",
            "email": "john@test.com",
            "phone": "03001234567",
            "is_active": True,
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "john@test.com"
    assert data["full_name"] == "John Doe"
    assert data["id"] is not None


def test_get_customer_happy_path(client, db, admin_token):
    """Admin fetches existing customer → 200 with correct data."""
    customer = make_customer(db)

    response = client.get(
        f"/customers/{customer.id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == customer.id
    assert data["email"] == customer.email


def test_list_customers_happy_path(client, db, admin_token):
    """Admin lists customers → 200 with results."""
    make_customer(db, email="one@test.com")
    make_customer(db, email="two@test.com")

    response = client.get(
        "/customers/",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2


def test_update_customer_happy_path(client, db, admin_token):
    """Admin patches customer phone → 200 with updated data."""
    customer = make_customer(db)

    response = client.patch(
        f"/customers/{customer.id}",
        json={"phone": "03009999999"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["phone"] == "03009999999"
    # other fields unchanged
    assert response.json()["email"] == customer.email


def test_delete_customer_happy_path(client, db, admin_token):
    """Admin deletes customer with no leads → 204."""
    customer = make_customer(db)

    response = client.delete(
        f"/customers/{customer.id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 204


# ── Not Found ──────────────────────────────────────────────────

def test_get_customer_not_found(client, db, admin_token):
    """Fetching non-existent customer → 404."""
    response = client.get(
        "/customers/999",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404
    assert "not found" in response.json()["message"].lower()


def test_update_customer_not_found(client, db, admin_token):
    """Patching non-existent customer → 404."""
    response = client.patch(
        "/customers/999",
        json={"phone": "03001234567"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404


def test_delete_customer_not_found(client, db, admin_token):
    """Deleting non-existent customer → 404."""
    response = client.delete(
        "/customers/999",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404


# ── Business Rule Violations ───────────────────────────────────

def test_create_customer_duplicate_email(client, db, admin_token):
    """Creating customer with already registered email → 409."""
    make_customer(db, email="john@test.com")

    response = client.post(
        "/customers/",
        json={
            "full_name": "Another John",
            "email": "john@test.com",  # same email
            "phone": "03001234567",
            "is_active": True,
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 409
    assert "already registered" in response.json()["message"].lower()


def test_delete_customer_with_active_leads(client, db, admin_token, agent_user):
    """Deleting customer who has active leads → 409."""
    customer = make_customer(db)
    prop = make_property(db)
    make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.delete(
        f"/customers/{customer.id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 409
    assert "existing leads" in response.json()["message"].lower()


def test_create_customer_invalid_name(client, db, admin_token):
    """Creating customer with numeric name → 422 validation error."""
    response = client.post(
        "/customers/",
        json={
            "full_name": "12345",  # invalid — numbers not allowed
            "email": "test@test.com",
            "phone": "03001234567",
            "is_active": True,
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 422


def test_create_customer_invalid_phone(client, db, admin_token):
    """Creating customer with alphabetic phone → 422 validation error."""
    response = client.post(
        "/customers/",
        json={
            "full_name": "John Doe",
            "email": "test@test.com",
            "phone": "apples",  # invalid
            "is_active": True,
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 422


# ── Permission Denied ──────────────────────────────────────────

def test_agent_cannot_delete_customer(client, db, agent_token):
    """Agent tries to delete customer → 403."""
    customer = make_customer(db)

    response = client.delete(
        f"/customers/{customer.id}",
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 403
    assert "admins" in response.json()["message"].lower()


def test_customer_cannot_list_customers(client, db, customer_token):
    """Customer role tries to list customers → 403."""
    response = client.get(
        "/customers/",
        headers=auth_headers(customer_token),
    )
    assert response.status_code == 403


def test_customer_cannot_create_customer(client, db, customer_token):
    """Customer role tries to create customer → 403."""
    response = client.post(
        "/customers/",
        json={
            "full_name": "John Doe",
            "email": "john@test.com",
            "phone": "03001234567",
            "is_active": True,
        },
        headers=auth_headers(customer_token),
    )
    assert response.status_code == 403


def test_unauthenticated_cannot_access_customers(client, db):
    """No token → 401."""
    response = client.get("/customers/")
    assert response.status_code == 401


# ── PATCH only updates sent fields ─────────────────────────────

def test_patch_only_updates_sent_fields(client, db, admin_token):
    """
    PATCH with only phone → email and full_name unchanged.
    Tests exclude_unset=True behavior.
    """
    customer = make_customer(db)
    original_email = customer.email
    original_name = customer.full_name

    response = client.patch(
        f"/customers/{customer.id}",
        json={"phone": "03009999999"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "03009999999"
    assert data["email"] == original_email 
    assert data["full_name"] == original_name