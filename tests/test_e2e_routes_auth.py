import asyncio
from unittest.mock import Mock

import pytest
from sqlalchemy import select

from src.entity.models import User
from src.services.auth import auth_service
from tests.conftest import TestingSessionLocal

user_data = {"username": "test_name1", "email": "test1@email.com", "password": "4575865948"}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "password" not in data
    assert "avatar" in data


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.routes.auth.send_email", mock_send_email)
    response = client.post("api/auth/signup", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"


def test_not_confirmed_login(client):
    response = client.post("api/auth/login",
                           data={"username": user_data.get("email"), "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.post("api/auth/login",
                           data={"username": user_data.get("email"), "password": user_data.get("password")})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert "token_type" in data


def test_wrong_password_login(client):
    response = client.post("api/auth/login",
                           data={"username": user_data.get("email"), "password": "password"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


def test_wrong_email_login(client):
    response = client.post("api/auth/login",
                           data={"username": "email", "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


def test_validation_error_login(client):
    response = client.post("api/auth/login",
                           data={"password": user_data.get("password")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_refresh_token(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()
        headers = {"Authorization": f"Bearer {current_user.refresh_token}"}
    response = client.get("api/auth/refresh_token", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" is not None
    assert "refresh_token" is not None
    assert "token_type" in data


def test_wrong_refresh_token(client):
    invalid_refresh_token = asyncio.run(
            auth_service.create_refresh_token(data={"sub": user_data.get("email")}, expires_delta=100)
        )
    headers = {"Authorization": f"Bearer {invalid_refresh_token}"}
    response = client.get("/api/auth/refresh_token", headers=headers)
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid refresh token"


def test_confirmed_email(client, monkeypatch):
    async def mock_get_email_from_token(token):
        return user_data["email"]

    monkeypatch.setattr("src.routes.auth.auth_service.get_email_from_token", mock_get_email_from_token)

    response = client.get(f"api/auth/confirmed_email/{user_data['email']}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "message" in data


@pytest.mark.asyncio
async def test_confirmed_email_already_confirmed(client, monkeypatch):
    async def mock_get_email_from_token(token):
        return user_data["email"]

    monkeypatch.setattr("src.routes.auth.auth_service.get_email_from_token", mock_get_email_from_token)
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).filter(User.email == user_data["email"]))
        current_user = current_user.scalar_one_or_none()
        if current_user:
            current_user.confirmed = True
            await session.commit()

    response = client.get(f"api/auth/confirmed_email/{user_data['email']}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "message" in data
    assert data["message"] == "Your email is already confirmed"


@pytest.mark.asyncio
async def test_confirmed_email_verification_error(client, monkeypatch):
    async def mock_get_email_from_token(token):
        return user_data["email"]

    monkeypatch.setattr("src.routes.auth.auth_service.get_email_from_token", mock_get_email_from_token)
    async with TestingSessionLocal() as session:
        response = client.get(f"api/auth/confirmed_email/invalid_token")
        assert response.status_code == 200, response.text
        data = response.json()
        assert "message" in data
        assert data["message"] == "Your email is already confirmed"


def test_request_email_already_confirmed(client, monkeypatch):
    response = client.post("api/auth/request_email", json={"email": user_data["email"]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert "message" in data
    assert data["message"] == "Your email is already confirmed"
