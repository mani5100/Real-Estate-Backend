from real_estate_backend.customers.model import Customer
from real_estate_backend.users.model import User


def create_customer_profile(
    client,
    user_headers: dict[str, str],
    phone: str | None = "+923001234567",
):
    return client.post(
        "/customers/me",
        headers=user_headers,
        json={"phone": phone},
    )


def test_user_can_create_customer_profile(
    client,
    normal_user,
    user_headers,
):
    response = create_customer_profile(
        client=client,
        user_headers=user_headers,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["user_id"] == normal_user.id
    assert body["phone"] == "+923001234567"

    assert body["user"]["id"] == normal_user.id
    assert body["user"]["email"] == normal_user.email
    assert body["user"]["full_name"] == normal_user.full_name
    assert body["user"]["is_active"] is True


def test_customer_profile_can_be_created_without_phone(
    client,
    normal_user,
    user_headers,
):
    response = create_customer_profile(
        client=client,
        user_headers=user_headers,
        phone=None,
    )

    assert response.status_code == 201

    body = response.json()

    assert body["user_id"] == normal_user.id
    assert body["phone"] is None


def test_customer_profile_rejects_invalid_phone(
    client,
    user_headers,
):
    response = client.post(
        "/customers/me",
        headers=user_headers,
        json={
            "phone": "invalid-phone!",
        },
    )

    assert response.status_code == 422


def test_customer_profile_rejects_unknown_fields(
    client,
    user_headers,
):
    response = client.post(
        "/customers/me",
        headers=user_headers,
        json={
            "phone": "+923001234567",
            "email": "other@example.com",
        },
    )

    assert response.status_code == 422


def test_user_cannot_create_two_customer_profiles(
    client,
    user_headers,
):
    first_response = create_customer_profile(
        client=client,
        user_headers=user_headers,
    )

    second_response = create_customer_profile(
        client=client,
        user_headers=user_headers,
        phone="+923009998888",
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_unauthenticated_user_cannot_create_customer_profile(
    client,
):
    response = client.post(
        "/customers/me",
        json={
            "phone": "+923001234567",
        },
    )

    assert response.status_code == 401


def test_get_my_customer_profile_returns_404_when_missing(
    client,
    user_headers,
):
    response = client.get(
        "/customers/me",
        headers=user_headers,
    )

    assert response.status_code == 404


def test_user_can_get_customer_profile(
    client,
    normal_user,
    user_headers,
):
    create_response = create_customer_profile(
        client=client,
        user_headers=user_headers,
    )

    assert create_response.status_code == 201

    response = client.get(
        "/customers/me",
        headers=user_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["user_id"] == normal_user.id
    assert body["phone"] == "+923001234567"
    assert body["user"]["email"] == normal_user.email


def test_unauthenticated_user_cannot_get_customer_profile(
    client,
):
    response = client.get("/customers/me")

    assert response.status_code == 401


def test_user_can_update_customer_profile(
    client,
    user_headers,
):
    create_response = create_customer_profile(
        client=client,
        user_headers=user_headers,
    )

    assert create_response.status_code == 201

    response = client.patch(
        "/customers/me",
        headers=user_headers,
        json={
            "phone": "+923009998888",
        },
    )

    assert response.status_code == 200
    assert response.json()["phone"] == "+923009998888"


def test_user_can_clear_customer_phone(
    client,
    user_headers,
):
    create_response = create_customer_profile(
        client=client,
        user_headers=user_headers,
    )

    assert create_response.status_code == 201

    response = client.patch(
        "/customers/me",
        headers=user_headers,
        json={
            "phone": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["phone"] is None


def test_empty_phone_is_normalized_to_none(
    client,
    user_headers,
):
    create_response = create_customer_profile(
        client=client,
        user_headers=user_headers,
    )

    assert create_response.status_code == 201

    response = client.patch(
        "/customers/me",
        headers=user_headers,
        json={
            "phone": "",
        },
    )

    assert response.status_code == 200
    assert response.json()["phone"] is None


def test_update_customer_profile_returns_404_when_missing(
    client,
    user_headers,
):
    response = client.patch(
        "/customers/me",
        headers=user_headers,
        json={
            "phone": "+923009998888",
        },
    )

    assert response.status_code == 404


def test_customer_update_rejects_invalid_phone(
    client,
    user_headers,
):
    create_response = create_customer_profile(
        client=client,
        user_headers=user_headers,
    )

    assert create_response.status_code == 201

    response = client.patch(
        "/customers/me",
        headers=user_headers,
        json={
            "phone": "not-valid!",
        },
    )

    assert response.status_code == 422


def test_unauthenticated_user_cannot_update_customer_profile(
    client,
):
    response = client.patch(
        "/customers/me",
        json={
            "phone": "+923009998888",
        },
    )

    assert response.status_code == 401


def test_admin_can_list_customers(
    client,
    db_session,
    admin_headers,
    normal_user,
):
    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    response = client.get(
        "/customers/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["next_cursor"] is None
    assert len(body["results"]) == 1

    result = body["results"][0]

    assert result["id"] == customer.id
    assert result["user_id"] == normal_user.id
    assert result["phone"] == "+923001234567"

    assert result["user"]["id"] == normal_user.id
    assert result["user"]["email"] == normal_user.email
    assert result["user"]["full_name"] == normal_user.full_name
    assert result["user"]["is_active"] is True


def test_admin_can_search_customers_by_full_name(
    client,
    db_session,
    admin_headers,
    normal_user,
):
    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()

    response = client.get(
        "/customers/",
        headers=admin_headers,
        params={
            "search": normal_user.full_name,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["results"]) == 1
    assert body["results"][0]["user"]["id"] == normal_user.id


def test_admin_can_search_customers_by_email(
    client,
    db_session,
    admin_headers,
    normal_user,
):
    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()

    response = client.get(
        "/customers/",
        headers=admin_headers,
        params={
            "search": normal_user.email,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["results"]) == 1
    assert body["results"][0]["user"]["email"] == normal_user.email


def test_admin_can_search_customers_by_phone(
    client,
    db_session,
    admin_headers,
    normal_user,
):
    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()

    response = client.get(
        "/customers/",
        headers=admin_headers,
        params={
            "search": "1234567",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["results"]) == 1
    assert body["results"][0]["phone"] == "+923001234567"


def test_admin_can_filter_active_customers(
    client,
    db_session,
    admin_headers,
    normal_user,
):
    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()

    response = client.get(
        "/customers/",
        headers=admin_headers,
        params={
            "is_active": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert len(body["results"]) == 1


def test_admin_active_filter_excludes_inactive_users(
    client,
    db_session,
    admin_headers,
    normal_user,
):
    normal_user.is_active = False

    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()

    response = client.get(
        "/customers/",
        headers=admin_headers,
        params={
            "is_active": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 0
    assert body["results"] == []


def test_normal_user_cannot_list_all_customers(
    client,
    user_headers,
):
    response = client.get(
        "/customers/",
        headers=user_headers,
    )

    assert response.status_code == 403


def test_unauthenticated_user_cannot_list_customers(
    client,
):
    response = client.get("/customers/")

    assert response.status_code == 401


def test_admin_can_get_customer_by_id(
    client,
    db_session,
    admin_headers,
    normal_user,
):
    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    response = client.get(
        f"/customers/{customer.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == customer.id
    assert body["user_id"] == normal_user.id
    assert body["user"]["email"] == normal_user.email


def test_admin_get_customer_returns_404(
    client,
    admin_headers,
):
    response = client.get(
        "/customers/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_normal_user_cannot_get_customer_by_id(
    client,
    db_session,
    user_headers,
    normal_user,
):
    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    response = client.get(
        f"/customers/{customer.id}",
        headers=user_headers,
    )

    assert response.status_code == 403


def test_admin_can_delete_customer_profile(
    client,
    db_session,
    admin_headers,
    normal_user,
):
    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    customer_id = customer.id
    user_id = normal_user.id

    response = client.delete(
        f"/customers/{customer_id}",
        headers=admin_headers,
    )

    assert response.status_code == 204
    assert response.content == b""

    db_session.expire_all()

    deleted_customer = db_session.get(Customer, customer_id)
    existing_user = db_session.get(User, user_id)

    assert deleted_customer is None
    assert existing_user is not None


def test_admin_delete_customer_returns_404(
    client,
    admin_headers,
):
    response = client.delete(
        "/customers/999999",
        headers=admin_headers,
    )

    assert response.status_code == 404


def test_normal_user_cannot_delete_customer_profile(
    client,
    db_session,
    user_headers,
    normal_user,
):
    customer = Customer(
        user_id=normal_user.id,
        phone="+923001234567",
    )

    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    response = client.delete(
        f"/customers/{customer.id}",
        headers=user_headers,
    )

    assert response.status_code == 403