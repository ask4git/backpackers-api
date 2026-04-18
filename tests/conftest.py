import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.spot import Spot
from app.models.user import User


# ── Engine ─────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def engine():
    return create_async_engine(settings.DATABASE_URL, echo=False)


@pytest.fixture(scope="session", autouse=True)
async def create_tables(engine):
    """세션 시작 시 스키마 생성, 종료 시 삭제."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# ── DB 세션 ────────────────────────────────────────────────────────────────────

@pytest.fixture
async def db(engine) -> AsyncSession:
    """테스트마다 새 세션. 테스트 후 모든 데이터 truncate."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.execute(
            text("TRUNCATE spot_reviews, spot_business_info, spots, users RESTART IDENTITY CASCADE")
        )
        await session.commit()


# ── HTTP 클라이언트 ────────────────────────────────────────────────────────────

@pytest.fixture
async def client(db) -> AsyncClient:
    """DB 세션을 주입한 테스트용 AsyncClient."""
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ── 유저 픽스처 ────────────────────────────────────────────────────────────────

@pytest.fixture
async def user(db) -> User:
    """일반 유저 (이메일/패스워드)."""
    u = User(
        email="user@example.com",
        hashed_password=hash_password("password123"),
        name="테스트유저",
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest.fixture
async def another_user(db) -> User:
    """두 번째 유저 (중복 리뷰 테스트용)."""
    u = User(
        email="another@example.com",
        hashed_password=hash_password("password123"),
        name="다른유저",
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest.fixture
def auth_headers(user) -> dict:
    """유저의 Bearer 토큰 헤더."""
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def another_auth_headers(another_user) -> dict:
    token = create_access_token({"sub": str(another_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ── 스팟 픽스처 ────────────────────────────────────────────────────────────────

@pytest.fixture
async def spot(db) -> Spot:
    """테스트용 스팟."""
    s = Spot(
        title="테스트 캠핑장",
        region_province="강원",
        region_city="속초시",
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s
