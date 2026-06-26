from fastapi import status

from app.models import User


def test_register_success(test_db_client, test_session):
    raw_password = "strong-password"
    user_data = {
        "email": "user@example.com",
        "username": "john",
        "password": raw_password,
    }

    register_response = test_db_client.post(
        "/api/v1/auth/register/",
        json=user_data,
    )
    response_data = register_response.json()
    user = test_session.get(User, response_data.get("id"))

    assert register_response.status_code == status.HTTP_201_CREATED
    assert "id" in response_data
    assert "email" in response_data
    assert "username" in response_data
    assert "is_active" in response_data
    assert "created_at" in response_data
    assert "updated_at" in response_data
    assert "password" not in response_data
    assert "hashed_password" not in response_data
    assert user is not None


def test_register_duplicate_email(test_db_client, first_user):
    second_user_data = {
        "email": "first_user@example.com",
        "username": "vader",
        "password": "raw_password",
    }
    register_response = test_db_client.post(
        "/api/v1/auth/register/",
        json=second_user_data,
    )

    assert register_response.status_code == status.HTTP_400_BAD_REQUEST
    assert register_response.json()["detail"] == "Данный email уже занят другим пользователем"


def test_register_duplicate_username(test_db_client, first_user):
    second_user_data = {
        "email": "second_user@example.com",
        "username": "igor",
        "password": "raw_password",
    }
    register_response = test_db_client.post(
        "/api/v1/auth/register/",
        json=second_user_data,
    )

    assert register_response.status_code == status.HTTP_400_BAD_REQUEST
    assert register_response.json()["detail"] == "Данный username уже занят другим пользователем"


def test_login_success(test_db_client, first_user):
    login_response = test_db_client.post(
        "/api/v1/auth/login/",
        data={
            "username": first_user.username,
            "password": "hard_password",
        },
    )
    login_response_data = login_response.json()

    assert login_response.status_code == status.HTTP_200_OK
    assert "access_token" in login_response_data
    assert login_response_data["access_token"] is not None
    assert login_response_data["token_type"] == "bearer"


def test_login_wrong_password(test_db_client, first_user):
    login_response = test_db_client.post(
        "/api/v1/auth/login/",
        data={
            "username": first_user.username,
            "password": "no_hard_password",
        },
    )

    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_unknown_user(test_db_client):
    login_response = test_db_client.post(
        "/api/v1/auth/login/",
        data={
            "username": "not_auth",
            "password": "no_hard_password",
        },
    )

    assert login_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_success(test_db_client, first_user):
    login_response = test_db_client.post(
        "/api/v1/auth/login/",
        data={
            "username": first_user.username,
            "password": "hard_password",
        },
    )
    token = login_response.json()["access_token"]

    me_response = test_db_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    me_response_data = me_response.json()

    assert me_response.status_code == status.HTTP_200_OK
    assert "id" in me_response_data
    assert "email" in me_response_data
    assert "username" in me_response_data
    assert "is_active" in me_response_data
    assert "created_at" in me_response_data
    assert "updated_at" in me_response_data
    assert me_response_data["email"] is not None
    assert me_response_data["username"] is not None
    assert me_response_data["email"] == first_user.email
    assert me_response_data["username"] == first_user.username


def test_get_me_without_token(test_db_client):
    me_response = test_db_client.get("/api/v1/auth/me")

    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_me_invalid_token(test_db_client):
    me_response = test_db_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert me_response.status_code == status.HTTP_401_UNAUTHORIZED
