# 테스트 전략

> 작성일: 2026-04-18  
> 현재 상태: **테스트 코드 없음 (커버리지 0%)** — 이 문서는 구현 전 전략 정의

---

## 목차
1. [기본 방침](#1-기본-방침)
2. [도구 & 의존성](#2-도구--의존성)
3. [디렉토리 구조](#3-디렉토리-구조)
4. [DB 격리 전략](#4-db-격리-전략)
5. [환경 설정](#5-환경-설정)
6. [conftest.py 설계](#6-conftestpy-설계)
7. [테스트 케이스 목록](#7-테스트-케이스-목록)
8. [커버리지 목표](#8-커버리지-목표)
9. [CI 연동](#9-ci-연동)
10. [구현 순서](#10-구현-순서)

---

## 1. 기본 방침

### 왜 통합 테스트 우선인가

이 프로젝트는 PostgreSQL 전용 타입을 적극 사용한다.

| 기능 | PostgreSQL 전용 |
|---|---|
| PK 타입 | `UUID` (PostgreSQL dialect) |
| 배열 컬럼 | `ARRAY(String)` |
| DB 레벨 제약 | `CHECK (rating >= 0 AND rating <= 5)` |
| 고유 제약 | `UNIQUE (spot_uid, user_id)` |

SQLite 인메모리로 대체하면 이 제약들이 동작하지 않아 **테스트가 통과해도 실제 운영에서 터지는** 상황이 발생할 수 있다. 따라서:

- **실제 PostgreSQL** 테스트 전용 DB 사용
- `httpx.AsyncClient`로 API를 엔드-투-엔드 호출하는 **통합 테스트** 중심
- 단위 테스트(mock)는 외부 의존성(Google OAuth)에만 제한적으로 사용

### 테스트 범위

```
[Client] → routers → crud → DB
              ↑
     여기서 테스트 (AsyncClient)
```

- **routers**: 모든 엔드포인트의 정상/실패 케이스
- **crud**: 라우터 테스트로 간접 검증 (별도 단위 테스트 작성 안 함)
- **core/security**: 토큰 생성/검증은 auth 테스트로 간접 검증
- **외부 API (Google)**: mock으로 대체

---

## 2. 도구 & 의존성

### 추가 필요 패키지 (dev 의존성)

```bash
uv add --dev pytest pytest-asyncio pytest-cov
# httpx는 이미 프로젝트 의존성에 포함됨
```

`pyproject.toml` 결과:
```toml
[dependency-groups]
dev = [
    "ruff>=0.15.11",
    "pytest>=8.0",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5.0",
]
```

### 각 도구의 역할

| 도구 | 역할 |
|---|---|
| `pytest` | 테스트 수집·실행·리포트 |
| `pytest-asyncio` | `async def test_*` 함수 지원 |
| `pytest-cov` | 커버리지 측정 (`--cov=app`) |
| `httpx.AsyncClient` | FastAPI 앱에 실제 HTTP 요청 전송 |

### pytest 설정 (`pyproject.toml`에 추가)

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"          # 모든 async 테스트 자동 인식
testpaths = ["tests"]
env = ["ENV_FILE=.env.test"]   # 테스트 전용 환경변수 파일
```

---

## 3. 디렉토리 구조

```
tests/
├── conftest.py          # 공통 픽스처 (DB, app, 인증 토큰 등)
├── test_auth.py         # POST /auth/register, /auth/login, /auth/google/verify
└── test_reviews.py      # GET/POST /spots/{spot_uid}/reviews
```

> 엔드포인트가 늘어나면 파일 추가. 예: `test_spots.py` (spots CRUD 라우터 생길 때)

---

## 4. DB 격리 전략

### 방식: 테스트 전용 DB + 테이블 truncate per test

**테스트 전용 DB** (`backpackers_test`) 를 docker-compose PostgreSQL에 별도 생성.

```sql
-- 최초 1회 실행
CREATE DATABASE backpackers_test;
```

**격리 단위**: 각 테스트 함수마다 관련 테이블을 `TRUNCATE ... RESTART IDENTITY CASCADE` 로 초기화.

> **트랜잭션 롤백 방식 대신 truncate를 선택한 이유**  
> `asyncpg` + SQLAlchemy async 환경에서는 nested transaction(savepoint) 설정이 복잡하고,  
> `httpx.AsyncClient`가 별도 connection을 사용하기 때문에 픽스처의 트랜잭션과 공유가 안 된다.  
> truncate가 더 단순하고 확실하다.

### DB 스키마 초기화

테스트 세션 시작 시 alembic `upgrade head` 실행 → 테스트 종료 시 `downgrade base` (선택).  
또는 `Base.metadata.create_all` / `drop_all` 사용.

---

## 5. 환경 설정

### `.env.test` 파일 (신규 생성 필요)

```dotenv
# ===== 테스트 환경 =====
DB_HOST=localhost
DB_PORT=5433
DB_USER=postgres
DB_PASSWORD=password
DB_NAME=backpackers_test      # ← dev와 다른 DB

SECRET_KEY=test-secret-key-not-for-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

ADMIN_USERNAME=admin
ADMIN_PASSWORD=testpassword

GOOGLE_CLIENT_ID=test-google-client-id
CORS_ORIGINS=http://localhost:3000
```

> `.env.test`는 `.gitignore`에서 제외 가능 (비밀 정보 없으므로). 팀 공유 권장.

### Makefile에 추가할 명령

```makefile
test:           ## pytest 실행 (테스트 전용 DB)
    ENV_FILE=.env.test uv run pytest -v --cov=app --cov-report=term-missing

test-fast:      ## 커버리지 없이 빠르게 실행
    ENV_FILE=.env.test uv run pytest -v
```

---

## 6. conftest.py 설계

### 전체 구조

```python
# tests/conftest.py

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.main import app
from app.core.config import settings
from app.core.database import Base
from app.core.security import create_access_token
from app.models.user import User
from app.core.security import hash_password

# ── DB 픽스처 ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def engine():
    """테스트 세션 전체에서 공유하는 async engine."""
    return create_async_engine(settings.DATABASE_URL, echo=False)


@pytest.fixture(scope="session", autouse=True)
async def create_tables(engine):
    """세션 시작 시 테이블 생성, 종료 시 삭제."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db(engine) -> AsyncSession:
    """테스트마다 새 DB 세션. 테스트 후 모든 테이블 truncate."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        # 테스트 후 데이터 정리 (외래키 순서 고려)
        await session.execute(text("TRUNCATE spot_reviews, spot_business_info, spots, users RESTART IDENTITY CASCADE"))
        await session.commit()


# ── HTTP 클라이언트 픽스처 ────────────────────────────────────────────────

@pytest.fixture
async def client(db) -> AsyncClient:
    """테스트용 AsyncClient. DB 세션을 app에 주입."""
    from app.core.database import get_db

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ── 유저 & 인증 픽스처 ────────────────────────────────────────────────────

@pytest.fixture
async def user(db) -> User:
    """테스트용 일반 유저 생성."""
    u = User(
        email="test@example.com",
        hashed_password=hash_password("password123"),
        name="테스트유저",
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest.fixture
def auth_headers(user) -> dict:
    """Bearer 토큰 헤더 반환."""
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# ── 스팟 픽스처 ───────────────────────────────────────────────────────────

@pytest.fixture
async def spot(db):
    """테스트용 스팟 생성."""
    from app.models.spot import Spot
    s = Spot(title="테스트 캠핑장", region_province="강원", region_city="속초시")
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s
```

---

## 7. 테스트 케이스 목록

### P0 — 반드시 작성 (핵심 로직)

#### `test_auth.py`

| 테스트 함수 | 시나리오 | 검증 포인트 |
|---|---|---|
| `test_register_success` | 정상 회원가입 | status 201, `access_token` 존재, `user.email` 일치 |
| `test_register_duplicate_email` | 같은 이메일로 재가입 | status 400, 에러 메시지 확인 |
| `test_register_invalid_email` | 이메일 형식 오류 | status 422 |
| `test_login_success` | 정상 로그인 | status 200, `access_token` 존재 |
| `test_login_wrong_password` | 틀린 비밀번호 | status 401 |
| `test_login_nonexistent_email` | 없는 이메일 | status 401 |

#### `test_reviews.py`

| 테스트 함수 | 시나리오 | 검증 포인트 |
|---|---|---|
| `test_write_review_success` | 정상 리뷰 작성 | status 201, rating/content 일치, spot.rating_avg 갱신 확인 |
| `test_write_review_no_auth` | 토큰 없이 POST | status 401 |
| `test_write_review_duplicate` | 같은 스팟에 두 번 리뷰 | status 409 |
| `test_write_review_rating_too_high` | rating = 5.1 | status 422 (Pydantic 검증) |
| `test_write_review_rating_negative` | rating = -1 | status 422 |
| `test_write_review_no_content` | content 없이 rating만 | status 201 (content nullable) |
| `test_write_review_invalid_spot` | 없는 spot_uid | status 404 |
| `test_list_reviews_empty` | 리뷰 없는 스팟 조회 | status 200, `total=0`, `rating_avg=0.0` |
| `test_list_reviews_with_data` | 리뷰 있는 스팟 조회 | `total`, `rating_avg` 정확성 확인 |
| `test_list_reviews_rating_avg_accuracy` | 리뷰 2개 후 평균 확인 | `rating_avg == (r1 + r2) / 2` |

### P1 — 있으면 좋은 것

#### `test_auth.py` 추가

| 테스트 함수 | 시나리오 | 검증 포인트 |
|---|---|---|
| `test_google_verify_success` | Google 토큰 검증 성공 | `unittest.mock.patch`로 `verify_oauth2_token` mock, status 200 |
| `test_google_verify_invalid_token` | 잘못된 Google 토큰 | status 400 |
| `test_google_verify_new_user` | 신규 유저 자동 가입 | DB에 유저 생성 확인 |
| `test_google_verify_existing_user` | 기존 유저 재로그인 | DB에 중복 유저 생성 안 됨 |

#### `test_reviews.py` 추가

| 테스트 함수 | 시나리오 | 검증 포인트 |
|---|---|---|
| `test_list_reviews_pagination` | `?page=2&limit=1` | 두 번째 리뷰만 반환 |
| `test_list_reviews_order` | 최신순 정렬 | `items[0].created_at` 이 최신 |
| `test_invalid_token` | 만료/변조된 JWT | status 401 |

### P2 — 나중에 (라우터 추가 시)

- `test_spots.py`: `GET /spots`, `GET /spots/{uid}` (spots 라우터 생기면)

---

## 8. 커버리지 목표

```bash
make test
# → pytest --cov=app --cov-report=term-missing
```

| 단계 | 커버리지 목표 | 작업 범위 |
|---|---|---|
| P0 완료 후 | ~70% | auth + reviews 핵심 케이스 |
| P1 완료 후 | ~85% | Google OAuth mock + 엣지케이스 |
| spots 라우터 추가 후 | ~90% | spots 엔드포인트 테스트 추가 |

### 커버리지 제외 대상

운영 환경에서만 동작하는 코드, 외부 의존성 등은 측정에서 제외:

```toml
# pyproject.toml
[tool.coverage.run]
omit = [
    "app/admin.py",           # sqladmin UI — HTTP 테스트 범위 밖
    "alembic/*",              # 마이그레이션
    "scripts/*",
]
```

---

## 9. CI 연동

`.github/workflows/deploy.yml`에 테스트 step 추가. 테스트 실패 시 배포 중단.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: password
          POSTGRES_DB: backpackers_test
        ports:
          - 5433:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 5s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4

      - name: 의존성 설치
        run: uv sync --frozen

      - name: 마이그레이션 적용
        run: ENV_FILE=.env.test uv run alembic upgrade head

      - name: 테스트 실행
        run: ENV_FILE=.env.test uv run pytest -v --cov=app --cov-report=xml

      - name: 커버리지 업로드 (선택)
        uses: codecov/codecov-action@v4

  deploy:
    needs: test       # ← 테스트 통과 후에만 배포
    ...
```

> `.env.test`의 값들은 CI secrets 또는 GitHub environment variables로 관리.  
> 단, `SECRET_KEY`처럼 민감한 값만 secrets로, `DB_NAME` 등은 workflow 파일에 직접 작성해도 됨.

---

## 10. 구현 순서

작업할 때 이 순서대로 진행 권장.

```
1. 패키지 설치
   uv add --dev pytest pytest-asyncio pytest-cov

2. pyproject.toml 설정 추가
   [tool.pytest.ini_options] asyncio_mode = "auto", testpaths, coverage omit

3. .env.test 파일 생성
   (backpackers_test DB 미리 생성: CREATE DATABASE backpackers_test;)

4. Makefile test 커맨드 ENV_FILE 반영 확인

5. tests/conftest.py 작성
   engine, create_tables, db, client, user, auth_headers, spot 픽스처

6. tests/test_auth.py — P0 케이스 작성
7. tests/test_reviews.py — P0 케이스 작성

8. make test 실행 → 전체 통과 확인

9. P1 케이스 추가 (Google OAuth mock 등)

10. CI workflow에 test job 추가
```

---

## 주의사항

- `asyncio_mode = "auto"` 설정 시 모든 `async def test_*`가 자동으로 async 모드로 실행됨. `@pytest.mark.asyncio` 데코레이터 불필요.
- `app.dependency_overrides`는 테스트 후 반드시 `.clear()` 할 것. 픽스처의 `finally` 또는 `yield` 이후 처리 필수.
- Google OAuth 테스트는 `unittest.mock.patch("app.routers.auth.google_id_token.verify_oauth2_token")` 으로 mock 처리.
- `spot_reviews` truncate 시 `spots`, `users` 보다 먼저 해야 FK 제약 위반이 안 남. `CASCADE` 옵션 사용 권장.
