import pytest
from tests.conftest import make_customer, make_property, make_lead, auth_headers


# ── Happy Path ─────────────────────────────────────────────────

def test_create_lead_happy_path(client, db, agent_token, agent_user):
    """Agent creates lead → 201 with correct data."""
    customer = make_customer(db)
    prop = make_property(db)

    response = client.post(
        "/leads/",
        json={
            "customer_id": customer.id,
            "property_id": prop.id,
            "status": "new",
            "agent_id": agent_user.id,
            "notes": "Interested in buying",
        },
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["customer_id"] == customer.id
    assert data["property_id"] == prop.id
    assert data["status"] == "new"
    assert data["id"] is not None


def test_get_lead_happy_path(client, db, admin_token, agent_user):
    """Admin fetches lead by id → 200 with nested customer and property."""
    customer = make_customer(db)
    prop = make_property(db)
    lead = make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.get(
        f"/leads/{lead.id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == lead.id

    # Nested objects present — no N+1
    assert data["customer"]["id"] == customer.id
    assert data["property"]["id"] == prop.id


def test_list_leads_happy_path(client, db, admin_token, agent_user):
    """Admin lists all leads → 200 with total count."""
    customer = make_customer(db)
    prop = make_property(db)
    make_lead(db, customer.id, prop.id, agent_user.id)
    make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.get(
        "/leads/",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2


def test_update_lead_happy_path(client, db, admin_token, agent_user):
    """Admin updates lead status → 200 with updated status."""
    customer = make_customer(db)
    prop = make_property(db)
    lead = make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.patch(
        f"/leads/{lead.id}",
        json={"status": "contacted"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "contacted"


def test_delete_lead_happy_path(client, db, admin_token, agent_user):
    """Admin deletes lead → 204."""
    customer = make_customer(db)
    prop = make_property(db)
    lead = make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.delete(
        f"/leads/{lead.id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 204


# ── Not Found ──────────────────────────────────────────────────

def test_get_lead_not_found(client, db, admin_token):
    """Fetching non-existent lead → 404."""
    response = client.get(
        "/leads/999",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404
    assert "not found" in response.json()["message"].lower()


def test_update_lead_not_found(client, db, admin_token):
    """Patching non-existent lead → 404."""
    response = client.patch(
        "/leads/999",
        json={"status": "contacted"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404


def test_delete_lead_not_found(client, db, admin_token):
    """Deleting non-existent lead → 404."""
    response = client.delete(
        "/leads/999",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404


# ── Business Rule Violations ───────────────────────────────────

def test_create_lead_invalid_customer(client, db, agent_token, agent_user):
    """Creating lead with non-existent customer_id → 404."""
    prop = make_property(db)

    response = client.post(
        "/leads/",
        json={
            "customer_id": 999,  # does not exist
            "property_id": prop.id,
            "status": "new",
            "agent_id": agent_user.id,
            "notes": "Test",
        },
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 404
    assert "customer" in response.json()["message"].lower()


def test_create_lead_invalid_property(client, db, agent_token, agent_user):
    """Creating lead with non-existent property_id → 404."""
    customer = make_customer(db)

    response = client.post(
        "/leads/",
        json={
            "customer_id": customer.id,
            "property_id": 999,  # does not exist
            "status": "new",
            "agent_id": agent_user.id,
            "notes": "Test",
        },
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 404
    assert "property" in response.json()["message"].lower()


def test_lead_status_change_to_terminal(client, db, admin_token, agent_user):
    """
    Updating lead to terminal status (closed) → 200.
    Verifies event fires without error.
    """
    customer = make_customer(db)
    prop = make_property(db)
    lead = make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.patch(
        f"/leads/{lead.id}",
        json={"status": "closed"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "closed"


def test_lead_status_change_to_lost(client, db, admin_token, agent_user):
    """
    Updating lead to lost (another terminal state) → 200.
    """
    customer = make_customer(db)
    prop = make_property(db)
    lead = make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.patch(
        f"/leads/{lead.id}",
        json={"status": "lost"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["status"] == "lost"


# ── Permission Denied ──────────────────────────────────────────

def test_customer_cannot_list_leads(client, db, customer_token):
    """Customer tries to list leads → 403."""
    response = client.get(
        "/leads/",
        headers=auth_headers(customer_token),
    )
    assert response.status_code == 403


def test_customer_cannot_create_lead(client, db, customer_token, agent_user):
    """Customer tries to create lead → 403."""
    customer = make_customer(db)
    prop = make_property(db)

    response = client.post(
        "/leads/",
        json={
            "customer_id": customer.id,
            "property_id": prop.id,
            "status": "new",
            "agent_id": agent_user.id,
        },
        headers=auth_headers(customer_token),
    )
    assert response.status_code == 403


def test_agent_cannot_delete_lead(client, db, agent_token, agent_user):
    """Agent tries to delete lead → 403."""
    customer = make_customer(db)
    prop = make_property(db)
    lead = make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.delete(
        f"/leads/{lead.id}",
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 403


def test_agent_cannot_access_other_agents_lead(client, db, agent_user):
    """
    Agent tries to get lead assigned to different agent → 403.
    This is the ownership check.
    """
    from tests.conftest import create_user, get_token
    from real_estate_backend.core.enums import UserRole

    # Create second agent
    other_agent = create_user(db, "other@test.com", UserRole.AGENT, "Other Agent")
    other_agent_token = get_token(other_agent)

    # Lead assigned to agent_user — not other_agent
    customer = make_customer(db)
    prop = make_property(db)
    lead = make_lead(db, customer.id, prop.id, agent_user.id)

    # Other agent tries to access it
    response = client.get(
        f"/leads/{lead.id}",
        headers=auth_headers(other_agent_token),
    )
    assert response.status_code == 403
    assert "assigned to you" in response.json()["message"].lower()


def test_agent_can_access_own_lead(client, db, agent_token, agent_user):
    """Agent accesses their own lead → 200."""
    customer = make_customer(db)
    prop = make_property(db)
    lead = make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.get(
        f"/leads/{lead.id}",
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 200
    assert response.json()["id"] == lead.id


def test_agent_only_sees_own_leads_in_list(client, db, agent_token, agent_user):
    """
    Agent lists leads → only sees their own leads.
    Admin's lead is invisible to agent.
    """
    from tests.conftest import create_user, get_token
    from real_estate_backend.core.enums import UserRole

    other_agent = create_user(db, "other@test.com", UserRole.AGENT, "Other Agent")

    customer = make_customer(db)
    prop = make_property(db)

    # One lead for agent_user, one for other_agent
    make_lead(db, customer.id, prop.id, agent_user.id)
    make_lead(db, customer.id, prop.id, other_agent.id)

    response = client.get(
        "/leads/",
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 200
    data = response.json()

    # Agent sees only their own lead
    assert data["total"] == 1
    assert all(r["agent_id"] == agent_user.id for r in data["results"])


def test_admin_sees_all_leads(client, db, admin_token, agent_user):
    """Admin lists leads → sees all leads from all agents."""
    from tests.conftest import create_user
    from real_estate_backend.core.enums import UserRole

    other_agent = create_user(db, "other@test.com", UserRole.AGENT, "Other Agent")

    customer = make_customer(db)
    prop = make_property(db)

    make_lead(db, customer.id, prop.id, agent_user.id)
    make_lead(db, customer.id, prop.id, other_agent.id)

    response = client.get(
        "/leads/",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()

    # Admin sees both leads
    assert data["total"] == 2


def test_unauthenticated_cannot_access_leads(client, db):
    """No token → 401."""
    response = client.get("/leads/")
    assert response.status_code == 401


# ── PATCH only updates sent fields ─────────────────────────────

def test_patch_lead_only_updates_sent_fields(client, db, admin_token, agent_user):
    """PATCH status only → agent_id and notes unchanged."""
    customer = make_customer(db)
    prop = make_property(db)
    lead = make_lead(db, customer.id, prop.id, agent_user.id)
    original_notes = lead.notes

    response = client.patch(
        f"/leads/{lead.id}",
        json={"status": "qualified"},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "qualified"
    assert data["notes"] == original_notes      # unchanged ✅
    assert data["agent_id"] == agent_user.id    # unchanged ✅