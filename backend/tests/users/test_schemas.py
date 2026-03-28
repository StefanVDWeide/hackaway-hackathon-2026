"""Tests for user schemas."""

import pytest
from pydantic import ValidationError

from app.modules.users.schemas import TokenResponse, UserLogin, UserRead, UserRegister


def test_user_register_valid():
    data = UserRegister(
        email="test@example.com",
        password="secret",
        display_name="Test",
    )
    assert data.email == "test@example.com"
    assert data.latitude is None


def test_user_register_with_location():
    data = UserRegister(
        email="test@example.com",
        password="secret",
        display_name="Test",
        latitude=52.0,
        longitude=4.0,
    )
    assert data.latitude == 52.0


def test_user_register_invalid_email():
    with pytest.raises(ValidationError):
        UserRegister(
            email="not-an-email",
            password="secret",
            display_name="Test",
        )


def test_user_login_valid():
    data = UserLogin(email="test@example.com", password="pass")
    assert data.email == "test@example.com"


def test_token_response_default_type():
    resp = TokenResponse(access_token="abc123")
    assert resp.token_type == "bearer"
