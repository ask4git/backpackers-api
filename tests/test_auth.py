"""
POST /auth/register
POST /auth/login
POST /auth/google/verify
"""
from unittest.mock import patch

import pytest
from httpx import AsyncClient


# ── 회원가입 ───────────────────────────────────────────────────────────────────

async def test_register_success(client: AsyncClient):
    res = await client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "password123",
        "name": "신규유저",
    })
    assert res.status_code == 201
    body = res.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["name"] == "신규유저"
    assert "hashed_password" not in body["user"]


async def test_register_duplicate_email(client: AsyncClient, user):
    res = await client.post("/auth/register", json={
        "email": user.email,
        "password": "password123",
        "name": "중복유저",
    })
    assert res.status_code == 400
    assert "이메일" in res.json()["detail"]


async def test_register_invalid_email(client: AsyncClient):
    res = await client.post("/auth/register", json={
        "email": "not-an-email",
        "password": "password123",
        "name": "유저",
    })
    assert res.status_code == 422


async def test_register_missing_fields(client: AsyncClient):
    res = await client.post("/auth/register", json={"email": "a@b.com"})
    assert res.status_code == 422


# ── 로그인 ─────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient, user):
    res = await client.post("/auth/login", json={
        "email": user.email,
        "password": "password123",
    })
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["user"]["email"] == user.email


async def test_login_wrong_password(client: AsyncClient, user):
    res = await client.post("/auth/login", json={
        "email": user.email,
        "password": "wrongpassword",
    })
    assert res.status_code == 401
    assert "비밀번호" in res.json()["detail"]


async def test_login_nonexistent_email(client: AsyncClient):
    res = await client.post("/auth/login", json={
        "email": "ghost@example.com",
        "password": "password123",
    })
    assert res.status_code == 401


async def test_login_invalid_email_format(client: AsyncClient):
    res = await client.post("/auth/login", json={
        "email": "not-email",
        "password": "password123",
    })
    assert res.status_code == 422


# ── Google OAuth ───────────────────────────────────────────────────────────────

async def test_google_verify_success(client: AsyncClient):
    fake_idinfo = {
        "email": "google@example.com",
        "name": "구글유저",
    }
    with patch("app.routers.auth.google_id_token.verify_oauth2_token", return_value=fake_idinfo):
        res = await client.post("/auth/google/verify", json={"id_token": "fake-token"})

    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert body["user"]["email"] == "google@example.com"
    assert body["user"]["name"] == "구글유저"


async def test_google_verify_invalid_token(client: AsyncClient):
    with patch("app.routers.auth.google_id_token.verify_oauth2_token", side_effect=ValueError("bad token")):
        res = await client.post("/auth/google/verify", json={"id_token": "invalid"})

    assert res.status_code == 400
    assert "Google" in res.json()["detail"]


async def test_google_verify_creates_new_user(client: AsyncClient, db):
    """Google 로그인 시 신규 유저가 DB에 생성되는지 확인."""
    from sqlalchemy import select
    from app.models.user import User

    fake_idinfo = {"email": "brand-new@google.com", "name": "브랜드뉴"}
    with patch("app.routers.auth.google_id_token.verify_oauth2_token", return_value=fake_idinfo):
        res = await client.post("/auth/google/verify", json={"id_token": "token"})

    assert res.status_code == 200
    result = await db.execute(select(User).where(User.email == "brand-new@google.com"))
    assert result.scalar_one_or_none() is not None


async def test_google_verify_existing_user_no_duplicate(client: AsyncClient, user, db):
    """기존 이메일로 Google 로그인 시 유저가 중복 생성되지 않는지 확인."""
    from sqlalchemy import func, select
    from app.models.user import User

    fake_idinfo = {"email": user.email, "name": user.name}
    with patch("app.routers.auth.google_id_token.verify_oauth2_token", return_value=fake_idinfo):
        res = await client.post("/auth/google/verify", json={"id_token": "token"})

    assert res.status_code == 200
    result = await db.execute(select(func.count()).where(User.email == user.email))
    assert result.scalar() == 1
