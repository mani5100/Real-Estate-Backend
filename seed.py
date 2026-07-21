from real_estate_backend.core.enums import UserRole
from real_estate_backend.users.model import User


def test_signup_creates_normal_user(client, db_session):
    response = client.post(
        "/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "Password1",
            "full_name": "New User",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["email"] == "newuser@example.com"
    assert body["full_name"] == "New User"
    assert body["role"] == UserRole.USER.value
    assert body["is_active"] is True

    user = db_session.query(User).filter_by(
        email="newuser@example.com"
    ).one()

    assert user.role == UserRole.USER


def test_signup_does_not_accept_role(client):
    response = client.post(
        "/auth/signup",
        json={
            "email": "admin@example.com",
            "password": "Password1",
            "full_name": "Fake Admin",
            "role": "admin",
        },
    )

    assert response.status_code == 201
    assert response.json()["role"] == UserRole.USER.value