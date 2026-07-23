from real_estate_backend.core.enums import UserRole
from real_estate_backend.properties.model import Property

from tests.conftest import (
    auth_headers,
    create_user,
    make_property,
)


VALID_PROPERTY_PAYLOAD = {
    "title": "Modern Apartment",
    "city": "Lahore",
    "address": "12 Gulberg Street",
    "price": 5_000_000,
    "bedrooms": 3,
    "bathrooms": 2,
    "area_sqft": 1200,
    "is_available": True,
}


# ---------------------------------------------------------------------------
# Property creation
# ---------------------------------------------------------------------------


def test_agent_can_create_property(
    client,
    db,
    agent_user,
    agent_token,
    agent_profile,
):
    response = client.post(
        "/properties/",
        json=VALID_PROPERTY_PAYLOAD,
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["title"] == "Modern Apartment"
    assert body["city"] == "Lahore"
    assert body["address"] == "12 Gulberg Street"
    assert body["price"] == 5_000_000
    assert body["bedrooms"] == 3
    assert body["bathrooms"] == 2
    assert body["area_sqft"] == 1200
    assert body["is_available"] is True

    property_record = db.get(Property, body["id"])

    assert property_record is not None
    assert property_record.agent_id == agent_profile.id


def test_property_creation_uses_agent_profile_id(
    client,
    db,
    agent_user,
    agent_token,
    agent_profile,
):
    response = client.post(
        "/properties/",
        json=VALID_PROPERTY_PAYLOAD,
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 201

    property_record = db.get(
        Property,
        response.json()["id"],
    )

    assert property_record is not None
    assert property_record.agent_id == agent_profile.id

    # The property FK must reference AgentProfile, not User.
    # These values may occasionally be equal in a fresh test database,
    # so the relationship itself is also checked.
    assert property_record.agent.user_id == agent_user.id


def test_admin_cannot_create_property(
    client,
    admin_token,
):
    response = client.post(
        "/properties/",
        json=VALID_PROPERTY_PAYLOAD,
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 403


def test_normal_user_cannot_create_property(
    client,
    user_token,
):
    response = client.post(
        "/properties/",
        json=VALID_PROPERTY_PAYLOAD,
        headers=auth_headers(user_token),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_create_property(
    client,
):
    response = client.post(
        "/properties/",
        json=VALID_PROPERTY_PAYLOAD,
    )

    assert response.status_code == 401


def test_create_property_invalid_price(
    client,
    agent_token,
    agent_profile,
):
    payload = {
        **VALID_PROPERTY_PAYLOAD,
        "price": -1000,
    }

    response = client.post(
        "/properties/",
        json=payload,
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 422


def test_create_property_invalid_city(
    client,
    agent_token,
    agent_profile,
):
    payload = {
        **VALID_PROPERTY_PAYLOAD,
        "city": "12345",
    }

    response = client.post(
        "/properties/",
        json=payload,
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 422


def test_create_property_invalid_bedrooms(
    client,
    agent_token,
    agent_profile,
):
    payload = {
        **VALID_PROPERTY_PAYLOAD,
        "bedrooms": -1,
    }

    response = client.post(
        "/properties/",
        json=payload,
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 422


def test_create_property_invalid_bathrooms(
    client,
    agent_token,
    agent_profile,
):
    payload = {
        **VALID_PROPERTY_PAYLOAD,
        "bathrooms": -1,
    }

    response = client.post(
        "/properties/",
        json=payload,
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 422


def test_create_property_rejects_unknown_fields(
    client,
    agent_token,
    agent_profile,
):
    payload = {
        **VALID_PROPERTY_PAYLOAD,
        "agent_id": 999,
    }

    response = client.post(
        "/properties/",
        json=payload,
        headers=auth_headers(agent_token),
    )

    # This expects PropertyCreate to use ConfigDict(extra="forbid").
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Property listing and retrieval
# ---------------------------------------------------------------------------


def test_get_all_properties(
    client,
    db,
    agent_user,
):
    first_property = make_property(
        db,
        agent=agent_user,
        title="First Apartment",
        city="Lahore",
    )

    second_property = make_property(
        db,
        agent=agent_user,
        title="Second Apartment",
        city="Karachi",
    )

    response = client.get("/properties/")

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert len(body["results"]) == 2

    returned_ids = {
        item["id"]
        for item in body["results"]
    }

    assert first_property.id in returned_ids
    assert second_property.id in returned_ids


def test_get_property_by_id(
    client,
    db,
    agent_user,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    response = client.get(
        f"/properties/{property_record.id}"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == property_record.id
    assert body["title"] == property_record.title
    assert body["city"] == property_record.city


def test_get_property_by_id_returns_404(
    client,
):
    response = client.get(
        "/properties/999999"
    )

    assert response.status_code == 404


def test_filter_properties_by_city(
    client,
    db,
    agent_user,
):
    make_property(
        db,
        agent=agent_user,
        title="Lahore Property",
        city="Lahore",
    )

    make_property(
        db,
        agent=agent_user,
        title="Karachi Property",
        city="Karachi",
    )

    response = client.get(
        "/properties/",
        params={"city": "Lahore"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["results"]) == 1
    assert body["results"][0]["city"] == "Lahore"


def test_filter_properties_by_minimum_price(
    client,
    db,
    agent_user,
):
    make_property(
        db,
        agent=agent_user,
        title="Affordable Property",
        price=2_000_000,
    )

    make_property(
        db,
        agent=agent_user,
        title="Expensive Property",
        price=8_000_000,
    )

    response = client.get(
        "/properties/",
        params={"min_price": 5_000_000},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["results"][0]["price"] == 8_000_000


def test_filter_properties_by_maximum_price(
    client,
    db,
    agent_user,
):
    make_property(
        db,
        agent=agent_user,
        title="Affordable Property",
        price=2_000_000,
    )

    make_property(
        db,
        agent=agent_user,
        title="Expensive Property",
        price=8_000_000,
    )

    response = client.get(
        "/properties/",
        params={"max_price": 5_000_000},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["results"][0]["price"] == 2_000_000


def test_filter_properties_by_minimum_bedrooms(
    client,
    db,
    agent_user,
):
    make_property(
        db,
        agent=agent_user,
        title="Small Property",
        bedrooms=1,
    )

    make_property(
        db,
        agent=agent_user,
        title="Large Property",
        bedrooms=4,
    )

    response = client.get(
        "/properties/",
        params={"min_bedrooms": 3},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["results"][0]["bedrooms"] == 4


def test_filter_available_properties(
    client,
    db,
    agent_user,
):
    make_property(
        db,
        agent=agent_user,
        title="Available Property",
        is_available=True,
    )

    make_property(
        db,
        agent=agent_user,
        title="Unavailable Property",
        is_available=False,
    )

    response = client.get(
        "/properties/",
        params={"is_available": True},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["results"][0]["is_available"] is True


def test_property_cursor_pagination(
    client,
    db,
    agent_user,
):
    first = make_property(
        db,
        agent=agent_user,
        title="First Property",
    )

    second = make_property(
        db,
        agent=agent_user,
        title="Second Property",
    )

    third = make_property(
        db,
        agent=agent_user,
        title="Third Property",
    )

    first_page = client.get(
        "/properties/",
        params={"limit": 2},
    )

    assert first_page.status_code == 200

    first_body = first_page.json()

    assert first_body["total"] == 3
    assert len(first_body["results"]) == 2
    assert first_body["next_cursor"] == second.id

    second_page = client.get(
        "/properties/",
        params={
            "limit": 2,
            "cursor": first_body["next_cursor"],
        },
    )

    assert second_page.status_code == 200

    second_body = second_page.json()

    assert second_body["total"] == 3
    assert len(second_body["results"]) == 1
    assert second_body["results"][0]["id"] == third.id
    assert second_body["next_cursor"] is None

    assert first.id < second.id < third.id


# ---------------------------------------------------------------------------
# Property update authorization
# ---------------------------------------------------------------------------


def test_agent_can_update_own_property(
    client,
    db,
    agent_user,
    agent_token,
    agent_profile,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    response = client.patch(
        f"/properties/{property_record.id}",
        json={
            "price": 9_999_999,
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 200
    assert response.json()["price"] == 9_999_999

    db.refresh(property_record)

    assert property_record.price == 9_999_999


def test_agent_cannot_update_another_agents_property(
    client,
    db,
    agent_token,
    agent_profile,
):
    other_agent = create_user(
        db=db,
        email="other-agent-update@test.com",
        role=UserRole.AGENT,
        full_name="Other Agent",
    )

    property_record = make_property(
        db,
        agent=other_agent,
    )

    response = client.patch(
        f"/properties/{property_record.id}",
        json={
            "price": 9_999_999,
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 403


def test_admin_can_update_any_property(
    client,
    db,
    agent_user,
    admin_token,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    response = client.patch(
        f"/properties/{property_record.id}",
        json={
            "price": 7_500_000,
        },
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 200
    assert response.json()["price"] == 7_500_000


def test_normal_user_cannot_update_property(
    client,
    db,
    agent_user,
    user_token,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    response = client.patch(
        f"/properties/{property_record.id}",
        json={
            "price": 7_500_000,
        },
        headers=auth_headers(user_token),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_update_property(
    client,
    db,
    agent_user,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    response = client.patch(
        f"/properties/{property_record.id}",
        json={
            "price": 7_500_000,
        },
    )

    assert response.status_code == 401


def test_update_missing_property_returns_404(
    client,
    admin_token,
):
    response = client.patch(
        "/properties/999999",
        json={
            "price": 7_500_000,
        },
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404


def test_update_property_rejects_invalid_price(
    client,
    db,
    agent_user,
    agent_token,
    agent_profile,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    response = client.patch(
        f"/properties/{property_record.id}",
        json={
            "price": -1,
        },
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Property delete authorization
# ---------------------------------------------------------------------------


def test_agent_can_delete_own_property(
    client,
    db,
    agent_user,
    agent_token,
    agent_profile,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    property_id = property_record.id

    response = client.delete(
        f"/properties/{property_id}",
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 204
    assert response.content == b""

    db.expire_all()

    assert db.get(Property, property_id) is None


def test_agent_cannot_delete_another_agents_property(
    client,
    db,
    agent_token,
    agent_profile,
):
    other_agent = create_user(
        db=db,
        email="other-agent-delete@test.com",
        role=UserRole.AGENT,
        full_name="Other Agent",
    )

    property_record = make_property(
        db,
        agent=other_agent,
    )

    response = client.delete(
        f"/properties/{property_record.id}",
        headers=auth_headers(agent_token),
    )

    assert response.status_code == 403


def test_admin_can_delete_any_property(
    client,
    db,
    agent_user,
    admin_token,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    property_id = property_record.id

    response = client.delete(
        f"/properties/{property_id}",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 204

    db.expire_all()

    assert db.get(Property, property_id) is None


def test_normal_user_cannot_delete_property(
    client,
    db,
    agent_user,
    user_token,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    response = client.delete(
        f"/properties/{property_record.id}",
        headers=auth_headers(user_token),
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_delete_property(
    client,
    db,
    agent_user,
):
    property_record = make_property(
        db,
        agent=agent_user,
    )

    response = client.delete(
        f"/properties/{property_record.id}"
    )

    assert response.status_code == 401


def test_delete_missing_property_returns_404(
    client,
    admin_token,
):
    response = client.delete(
        "/properties/999999",
        headers=auth_headers(admin_token),
    )

    assert response.status_code == 404