import pytest
from tests.conftest import make_customer, make_property, make_lead, auth_headers


# ── Happy Path ─────────────────────────────────────────────────

def test_create_property_happy_path(client, db, admin_token):
    """Admin creates property → 201 with correct data."""
    response = client.post(
        "/properties/",
        json={
            "title": "Modern Apartment",
            "city": "Lahore",
            "address": "12 Gulberg Street",
            "price": 5000000,
            "bedrooms": 3,
            "bathrooms": 2,
            "area_sqft": 1200,
            "is_available": True,
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Modern Apartment"
    assert data["city"] == "Lahore"
    assert data["id"] is not None


def test_get_property_happy_path(client, db, admin_token):
    """Fetch existing property → 200 with correct data."""
    prop = make_property(db)

    response = client.get(f"/properties/{prop.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == prop.id
    assert data["city"] == prop.city


def test_list_properties_happy_path(client, db):
    """List properties → 200 with total count."""
    make_property(db)
    make_property(db)

    response = client.get("/properties/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["results"]) == 2


def test_update_property_happy_path(client, db, admin_token):
    """Admin patches property price → 200 with updated data."""
    prop = make_property(db)

    response = client.patch(
        f"/properties/{prop.id}",
        json={"price": 9999999},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    assert response.json()["price"] == 9999999
    assert response.json()["city"] == prop.city  # unchanged


def test_delete_property_happy_path(client, db, admin_token):
    """Admin deletes property with no leads → 204."""
    prop = make_property(db)

    response = client.delete(
        f"/properties/{prop.id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 204


def test_get_properties_by_bedrooms_happy_path(client, db):
    """Filter properties by bedroom count → correct results."""
    make_property(db)  # 3 bedrooms by default

    response = client.get("/properties/bedrooms/3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(p["bedrooms"] == 3 for p in data)


# ── Not Found ──────────────────────────────────────────────────

def test_get_property_not_found(client, db):
    """Fetching non-existent property → 404."""
    response = client.get("/properties/999")
    assert response.status_code == 404
    assert "not found" in response.json()["message"].lower()


def test_update_property_not_found(client, db, admin_token):
    """Patching non-existent property → 404."""
    response = client.patch(
        "/properties/999",
        json={"price": 1000000},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404


def test_delete_property_not_found(client, db, admin_token):
    """Deleting non-existent property → 404."""
    response = client.delete(
        "/properties/999",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 404


def test_get_properties_by_bedrooms_not_found(client, db):
    """No properties with given bedroom count → 404."""
    response = client.get("/properties/bedrooms/99")
    assert response.status_code == 404
    assert "99 bedrooms" in response.json()["message"].lower()


# ── Business Rule Violations ───────────────────────────────────

def test_delete_property_with_active_leads(client, db, admin_token, agent_user):
    """Deleting property that has active leads → 409."""
    customer = make_customer(db)
    prop = make_property(db)
    make_lead(db, customer.id, prop.id, agent_user.id)

    response = client.delete(
        f"/properties/{prop.id}",
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 409
    assert "existing leads" in response.json()["message"].lower()


def test_create_property_invalid_price(client, db, admin_token):
    """Creating property with negative price → 422."""
    response = client.post(
        "/properties/",
        json={
            "title": "Test Property",
            "city": "Lahore",
            "address": "12 Gulberg Street",
            "price": -1000,  # invalid
            "bedrooms": 3,
            "bathrooms": 2,
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 422


def test_create_property_invalid_city(client, db, admin_token):
    """Creating property with numeric city → 422."""
    response = client.post(
        "/properties/",
        json={
            "title": "Test Property",
            "city": "12345",  # invalid
            "address": "12 Gulberg Street",
            "price": 5000000,
            "bedrooms": 3,
            "bathrooms": 2,
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 422


def test_create_property_invalid_bedrooms(client, db, admin_token):
    """Creating property with negative bedrooms → 422."""
    response = client.post(
        "/properties/",
        json={
            "title": "Test Property",
            "city": "Lahore",
            "address": "12 Gulberg Street",
            "price": 5000000,
            "bedrooms": -1,  # invalid
            "bathrooms": 2,
        },
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 422


# ── Filters ────────────────────────────────────────────────────

def test_filter_properties_by_city(client, db):
    """Filter by city → only matching properties returned."""
    make_property(db)  # city=Lahore by default

    response = client.get("/properties/?city=Lahore")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(p["city"] == "Lahore" for p in data["results"])


def test_filter_properties_by_min_price(client, db):
    """Filter by min_price → only properties above threshold."""
    make_property(db)  # price=5000000 by default

    response = client.get("/properties/?min_price=4000000")
    assert response.status_code == 200
    data = response.json()
    assert all(p["price"] >= 4000000 for p in data["results"])


def test_filter_properties_by_is_available(client, db):
    """Filter by availability → only available properties."""
    make_property(db)  # is_available=True by default

    response = client.get("/properties/?is_available=true")
    assert response.status_code == 200
    data = response.json()
    assert all(p["is_available"] is True for p in data["results"])


def test_filter_properties_no_results(client, db):
    """Filter with no matches → empty results with total 0."""
    make_property(db)

    response = client.get("/properties/?city=NonExistentCity")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["results"] == []


# ── Permission Denied ──────────────────────────────────────────

def test_customer_cannot_create_property(client, db, customer_token):
    """Customer tries to create property → 403."""
    response = client.post(
        "/properties/",
        json={
            "title": "Modern Apartment",
            "city": "Lahore",
            "address": "12 Gulberg Street",
            "price": 5000000,
            "bedrooms": 3,
            "bathrooms": 2,
        },
        headers=auth_headers(customer_token),
    )
    assert response.status_code == 403


def test_agent_cannot_delete_property(client, db, agent_token):
    """Agent tries to delete property → 403."""
    prop = make_property(db)

    response = client.delete(
        f"/properties/{prop.id}",
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 403


def test_agent_cannot_update_property(client, db, agent_token):
    """Agent tries to update property → 403."""
    prop = make_property(db)

    response = client.patch(
        f"/properties/{prop.id}",
        json={"price": 9999999},
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 403


def test_public_can_list_properties(client, db):
    """No token needed for listing properties → 200."""
    make_property(db)

    response = client.get("/properties/")
    assert response.status_code == 200


def test_public_can_get_property(client, db):
    """No token needed for single property → 200."""
    prop = make_property(db)

    response = client.get(f"/properties/{prop.id}")
    assert response.status_code == 200


# ── PATCH only updates sent fields ─────────────────────────────

def test_patch_only_updates_sent_fields(client, db, admin_token):
    """PATCH price only → city and title unchanged."""
    prop = make_property(db)
    original_city = prop.city
    original_title = prop.title

    response = client.patch(
        f"/properties/{prop.id}",
        json={"price": 9999999},
        headers=auth_headers(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == 9999999
    assert data["city"] == original_city    # unchanged ✅
    assert data["title"] == original_title  # unchanged ✅