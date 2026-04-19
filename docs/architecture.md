# Backpackers API — 아키텍처 & 개발 가이드

> 최종 업데이트: 2026-04-18  
> 현재 브랜치: `feature/admin-panel` (main 미merge 상태)

---

## 목차
1. [프로젝트 개요](#1-프로젝트-개요)
2. [기술 스택](#2-기술-스택)
3. [디렉토리 구조](#3-디렉토리-구조)
4. [환경 설정](#4-환경-설정)
5. [개발 환경 실행](#5-개발-환경-실행)
6. [데이터베이스 스키마](#6-데이터베이스-스키마)
7. [레이어 아키텍처](#7-레이어-아키텍처)
8. [API 엔드포인트](#8-api-엔드포인트)
9. [인증 시스템](#9-인증-시스템)
10. [어드민 패널](#10-어드민-패널)
11. [마이그레이션 히스토리](#11-마이그레이션-히스토리)
12. [Git 브랜치 규칙](#12-git-브랜치-규칙)
13. [코드 품질](#13-코드-품질)
14. [배포](#14-배포)
15. [남은 작업 / TODO](#15-남은-작업--todo)

---

## 1. 프로젝트 개요

국립공원·캠핑장 정보를 제공하는 FastAPI 기반 백엔드 API (POC 단계).

- 공공 데이터 기반 캠핑 스팟 정보 제공
- 사용자 인증 (이메일/패스워드, Google OAuth)
- 스팟별 리뷰·별점 시스템
- 운영팀용 웹 어드민 패널 (`/admin`)

---

## 2. 기술 스택

| 영역 | 기술 |
|---|---|
| 언어 | Python 3.12 |
| 웹 프레임워크 | FastAPI 0.115 |
| ORM | SQLAlchemy 2.0 (asyncio) |
| DB 드라이버 | asyncpg 0.29 |
| DB | PostgreSQL 16 |
| 마이그레이션 | Alembic 1.13 |
| 인증 | python-jose (JWT HS256), passlib bcrypt |
| Google OAuth | google-auth 2.35 |
| 어드민 패널 | sqladmin 0.24 |
| 패키지 관리 | uv |
| 린트/포맷 | ruff |
| 배포 | AWS Lightsail (컨테이너 서비스) |

---

## 3. 디렉토리 구조

```
backpackers-api/
├── app/
│   ├── main.py              # FastAPI 앱 진입점, Admin 마운트
│   ├── admin.py             # sqladmin ModelView 정의
│   ├── dependencies.py      # get_current_user (JWT 검증)
│   ├── core/
│   │   ├── config.py        # Settings (pydantic-settings, 환경변수)
│   │   ├── database.py      # async engine, AsyncSessionLocal, Base
│   │   └── security.py      # hash_password, verify_password, JWT 생성/검증
│   ├── models/
│   │   ├── __init__.py      # 모든 모델 import (alembic autogenerate용)
│   │   ├── user.py          # User
│   │   ├── spot.py          # Spot, SpotBusinessInfo
│   │   └── review.py        # SpotReview
│   ├── schemas/
│   │   ├── user.py          # UserRegister, UserLogin, UserResponse, TokenResponse, GoogleVerifyRequest
│   │   └── review.py        # ReviewCreate, ReviewResponse, ReviewListResponse
│   ├── crud/
│   │   ├── user.py          # get_user_by_email, get_user_by_id, create_user, get_or_create_google_user
│   │   └── review.py        # create_review, get_reviews_by_spot, _refresh_spot_rating
│   └── routers/
│       ├── auth.py          # /auth/register, /auth/login, /auth/google/verify
│       └── reviews.py       # /spots/{uid}/reviews (GET, POST)
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── d3c40504a639_create_initial_tables.py
│       ├── 5fb2a5359e9a_add_spots_and_spot_business_info_tables.py
│       ├── 24da437524a4_drop_camping_spots_and_spot_reports_.py
│       └── 4e7b6580fd0f_add_spot_reviews_table_and_rating_cache_.py
├── docs/
│   ├── architecture.md      # 이 파일
│   ├── erd.md               # Mermaid ERD + 필드 상세 테이블
│   ├── openapi.json         # OpenAPI 3.0.3 스펙 (Postman import용)
│   ├── api-reference.md
│   ├── deployment-progress.md
│   └── frontend-google-auth.md
├── pyproject.toml           # 의존성 (uv 관리)
├── Makefile                 # 자주 쓰는 명령어 래핑
├── docker-compose.yml       # 로컬 PostgreSQL (포트 5433)
├── .env.local               # 로컬 개발용 환경변수
└── .env.local.example       # 환경변수 템플릿
```

---

## 4. 환경 설정

### 환경변수 목록

`app/core/config.py`의 `Settings` 클래스가 관리. `.env.*` 파일에서 로드.

| 변수명 | 필수 | 기본값 | 설명 |
|---|---|---|---|
| `DB_HOST` | ✅ | — | PostgreSQL 호스트 |
| `DB_PORT` | ✅ | — | PostgreSQL 포트 |
| `DB_USER` | ✅ | — | DB 유저명 |
| `DB_PASSWORD` | ✅ | — | DB 패스워드 |
| `DB_NAME` | ✅ | — | DB 이름 |
| `SECRET_KEY` | ✅ | — | JWT 서명 키 (`make secret-gen`으로 생성) |
| `ALGORITHM` | — | `HS256` | JWT 알고리즘 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | — | `1440` | JWT 만료 (24시간) |
| `ADMIN_USERNAME` | — | `admin` | 어드민 패널 로그인 ID |
| `ADMIN_PASSWORD` | ✅ | `""` | 어드민 패널 로그인 PW (빈 값이면 /admin 접근 불가) |
| `GOOGLE_CLIENT_ID` | — | `""` | Google OAuth Client ID |
| `CORS_ORIGINS` | — | `http://localhost:3000,...` | 쉼표 구분 허용 오리진 목록 |
| `ENVIRONMENT` | — | 파일명 자동 추론 | `local` / `devel` / `prod` |

> `ENV_FILE` 환경변수로 어떤 `.env.*` 파일을 쓸지 결정. Makefile이 자동 주입.  
> 예: `make dev` → `ENV_FILE=.env.local`

### 환경 파일 종류

| 파일 | 용도 |
|---|---|
| `.env.local` | 로컬 개발 (docker-compose PostgreSQL) |
| `.env.devel` | devel 서버 연결 |
| `.env.prod` | prod DB 접근 (SSH 터널 필요) |

> `.env.*` 파일은 `.gitignore`에 포함. 팀원은 `.env.local.example` 복사해서 만들 것.

---

## 5. 개발 환경 실행

```bash
# 1. PostgreSQL 실행 (docker-compose, 포트 5433)
docker compose up -d

# 2. 마이그레이션 적용
make migrate

# 3. 서버 실행 (hot reload)
make dev
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI, local 환경만)
# → http://localhost:8000/admin (어드민 패널)
```

> 모든 Python 명령은 `uv run`으로 실행. `make` 명령이 래핑해줌.

### 자주 쓰는 Make 명령

| 명령 | 설명 |
|---|---|
| `make dev` | 로컬 서버 실행 (hot reload) |
| `make migrate` | alembic upgrade head |
| `make migrate-create MSG="설명"` | 새 마이그레이션 파일 생성 |
| `make migrate-down` | 한 단계 롤백 |
| `make lint` | ruff 린트 검사 |
| `make lint-fix` | ruff 자동 수정 |
| `make format` | ruff format |
| `make secret-gen` | 새 SECRET_KEY 생성 |
| `make tunnel` | prod DB SSH 터널 열기 |
| `make deploy LIGHTSAIL_IMAGE=...` | Lightsail 배포 |

---

## 6. 데이터베이스 스키마

> 상세 ERD는 `docs/erd.md` 참고.

### 테이블 관계

```
users ──────────────────────────┐
                                │ (user_id FK)
spots ──┬── spot_business_info  │
        │   (1:1, spot_uid FK)  │
        └── spot_reviews ───────┘
            (N:M 구조, spot_uid + user_id unique)
```

### users

| 필드 | 타입 | 비고 |
|---|---|---|
| id | UUID | PK |
| email | String | unique, indexed |
| hashed_password | String | bcrypt 해시. Google OAuth 유저는 `""` |
| name | String | |
| created_at / updated_at | DateTime(tz) | |

### spots

| 필드 | 타입 | 비고 |
|---|---|---|
| uid | UUID | PK |
| title | String | indexed |
| address / address_detail | String | nullable |
| region_province / region_city | String | nullable, indexed |
| postal_code / phone | String | nullable |
| description / tagline | String | nullable |
| latitude / longitude / altitude | Float | nullable |
| unit_count | Integer | 야영동 개수, nullable |
| is_fee_required / is_pet_allowed / has_equipment_rental | Boolean | nullable |
| pet_policy | String | nullable |
| themes / amenities / nearby_facilities | String[] | nullable, ARRAY 타입 |
| fire_pit_type / camp_sight_type | String | nullable |
| **rating_avg** | Float | 리뷰 생성 시 자동 갱신 캐시 |
| **review_count** | Integer | 리뷰 생성 시 자동 갱신 캐시 |
| created_at / updated_at | DateTime(tz) | |

### spot_business_info

| 필드 | 타입 | 비고 |
|---|---|---|
| uid | UUID | PK |
| spot_uid | UUID | FK → spots.uid, indexed |
| business_reg_no | String | 사업자번호, nullable |
| tourism_business_reg_no | String | 관광사업자번호, nullable |
| business_type / operation_type / operating_agency | String | nullable |
| operating_status | String | nullable, indexed |
| national_park_no | Integer | 국립공원관리번호, nullable |
| national_park_office_code / serial_no / category_code | String | nullable |
| licensed_at | Date | 인허가일자, nullable |
| created_at / updated_at | DateTime(tz) | |

### spot_reviews

| 필드 | 타입 | 비고 |
|---|---|---|
| uid | UUID | PK |
| spot_uid | UUID | FK → spots.uid, indexed |
| user_id | UUID | FK → users.id, indexed |
| rating | Float | CHECK 0 ≤ rating ≤ 5 |
| content | String | nullable |
| created_at / updated_at | DateTime(tz) | |

> DB 레벨 제약:
> - `CHECK (rating >= 0 AND rating <= 5)` → name: `check_review_rating_range`
> - `UNIQUE (spot_uid, user_id)` → name: `uq_spot_user_review` (스팟당 유저 1개 리뷰)

---

## 7. 레이어 아키텍처

```
routers/ ← HTTP 요청/응답, 의존성 주입만
  ↓
crud/    ← DB 쿼리 로직만 (비즈니스 로직 없음)
  ↓
models/  ← SQLAlchemy ORM 모델
```

- `schemas/`: Pydantic 입출력 모델 (routers가 사용)
- `core/`: 설정, DB 연결, 보안 유틸 (어디서든 참조 가능)
- `dependencies.py`: FastAPI `Depends()` 함수 모음

**레이어 간 규칙:**
- routers에서 직접 DB 쿼리 금지 → 반드시 crud 함수 호출
- crud에서 HTTP 개념(HTTPException 등) 사용 금지
- models에서 비즈니스 로직 금지

---

## 8. API 엔드포인트

### 인증 (`/auth`)

| Method | Path | 인증 | 설명 |
|---|---|---|---|
| `POST` | `/auth/register` | — | 이메일 회원가입 → JWT 반환 |
| `POST` | `/auth/login` | — | 이메일 로그인 → JWT 반환 |
| `POST` | `/auth/google/verify` | — | Google ID Token 검증 → JWT 반환 (신규면 자동 가입) |

**공통 응답 (`TokenResponse`):**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "uuid", "email": "...", "name": "...", "created_at": "..." }
}
```

### 리뷰 (`/spots`)

| Method | Path | 인증 | 설명 |
|---|---|---|---|
| `POST` | `/spots/{spot_uid}/reviews` | ✅ Bearer | 리뷰 작성. 중복 시 409, 없는 spot 시 404 |
| `GET` | `/spots/{spot_uid}/reviews` | — | 리뷰 목록 + 평균 별점 (`?page=1&limit=20`) |

**GET 응답 (`ReviewListResponse`):**
```json
{
  "items": [{ "uid": "...", "spot_uid": "...", "user_id": "...", "rating": 4.5, "content": "...", "created_at": "..." }],
  "total": 10,
  "rating_avg": 4.3
}
```

### 기타

| Method | Path | 설명 |
|---|---|---|
| `GET` | `/health` | 서버 상태 확인 |
| `GET` | `/docs` | Swagger UI (local/devel 환경만) |
| `GET` | `/admin` | 어드민 패널 (ID/PW 로그인) |

---

## 9. 인증 시스템

### JWT (이메일/패스워드)

- 알고리즘: HS256
- 만료: 24시간 (`ACCESS_TOKEN_EXPIRE_MINUTES=1440`)
- payload: `{ "sub": "<user_id_uuid>", "exp": ... }`
- 발급: 로그인/회원가입 성공 시
- 검증: `app/dependencies.py`의 `get_current_user`

```python
# 인증이 필요한 엔드포인트에 추가
current_user: User = Depends(get_current_user)
```

**버그 수정 이력:** `get_current_user`에서 `UUID(user_id)` 파싱 실패 시 try 블록 밖에서 `ValueError`가 발생해 500이 반환되던 문제 → try 블록 내에서 파싱하도록 수정.

### Google OAuth

- 프론트엔드가 Google로부터 ID Token을 직접 발급받아 서버에 전달
- 서버는 `google-auth` 라이브러리로 ID Token 검증 (`GOOGLE_CLIENT_ID` 필요)
- 검증 성공 시 이메일/이름으로 DB 조회 → 없으면 자동 생성 → JWT 발급
- Google OAuth 유저의 `hashed_password`는 `""` (패스워드 로그인 불가, 보안 홀 아님)

### 패스워드

- `passlib[bcrypt]` 사용
- `hash_password()` / `verify_password()` in `app/core/security.py`

---

## 10. 어드민 패널

**URL:** `http://localhost:8000/admin`  
**라이브러리:** sqladmin 0.24

### 로그인

환경변수 `ADMIN_USERNAME` / `ADMIN_PASSWORD`로 인증.  
`ADMIN_PASSWORD`가 빈 값이면 접근 자체 차단.

| 환경 | 기본값 |
|---|---|
| `.env.local` | `admin` / `admin1234` |
| `.env.prod` | 반드시 강한 패스워드 설정 필요 |

### 관리 메뉴

| 메뉴 | 모델 | 주요 기능 |
|---|---|---|
| 스팟 목록 | `Spot` | title/address 검색, rating/review_count/created_at 정렬 |
| 사업자 정보 | `SpotBusinessInfo` | operating_agency 검색, operating_status 정렬 |
| 리뷰 목록 | `SpotReview` | rating/created_at 정렬 |
| 사용자 목록 | `User` | email/name 검색, created_at 정렬 |

### 편집 제한 사항

- `spots`의 Array 컬럼(`themes`, `amenities`, `nearby_facilities`): form 제외 (sqladmin Array 편집 미지원)
- `users`의 `hashed_password`: form 제외 (보안)
- 어드민에서 직접 리뷰 수정 시 `spots.rating_avg`/`review_count` 자동 갱신 **안 됨** (API 경유 시에만 갱신) → 추후 개선 필요

---

## 11. 마이그레이션 히스토리

| 버전 | 설명 |
|---|---|
| `d3c40504` | 초기 테이블 생성 (users, camping_spots, spot_reports) |
| `5fb2a535` | spots, spot_business_info 테이블 추가 |
| `24da4375` | camping_spots, spot_reports 테이블 제거 |
| `4e7b6580` | spot_reviews 추가, spots에 rating_avg/review_count 컬럼 추가 |

### 새 마이그레이션 작성 규칙

```bash
# 모델 수정 후 반드시 아래 순서로
make migrate-create MSG="변경 내용 설명"  # 파일 생성
make migrate                              # 적용
```

> `alembic/versions/` 파일을 직접 편집하지 말 것.

---

## 12. Git 브랜치 규칙

- **main 직접 push 금지**
- 브랜치 네이밍: `feature/설명`, `fix/설명`
- 작업 완료 후 PR → main merge

```bash
git checkout -b feature/새기능
# 작업 후
git push origin feature/새기능
# GitHub에서 PR 생성
```

### 현재 열린 브랜치

| 브랜치 | 내용 | 상태 |
|---|---|---|
| `feature/update-openapi-spec` | openapi.json 갱신 | push됨, PR 미생성 |
| `feature/admin-panel` | sqladmin 어드민 패널 | push됨, PR 미생성 |

---

## 13. 코드 품질

```bash
make lint      # ruff 린트 검사
make lint-fix  # 자동 수정
make format    # ruff format 포맷
```

**규칙:**
- 코드 변경 후 반드시 `make lint` 실행
- 커밋 전 `make format` 실행
- 에러 메시지는 한국어
- 비동기(`async/await`) 패턴 유지
- `.env` 값 코드에 하드코딩 금지
- 새 라우터 추가 시 `app/main.py`에 `include_router` 등록

---

## 14. 배포

### 인프라

- AWS Lightsail 컨테이너 서비스
- 리전: `ap-northeast-2` (서울)
- 서비스명: `backpackers-api`

### 배포 흐름

```bash
make build                                  # Docker 이미지 빌드 (linux/amd64)
make push                                   # Lightsail에 이미지 push
make deploy LIGHTSAIL_IMAGE=':backpackers-api.backpackers-api.N'  # 배포
make status                                 # 배포 상태 확인
```

### CI/CD

`.github/workflows/` — GitHub Actions 기반 자동 배포 (push to main 트리거).  
→ 상세 내용은 `docs/deployment-progress.md` 참고.

---

## 15. 남은 작업 / TODO

### 단기 (다음 작업 우선순위)

- [ ] `feature/update-openapi-spec`, `feature/admin-panel` 브랜치 PR → main merge
- [ ] spots 조회 API 추가 (`GET /spots`, `GET /spots/{uid}`) — 현재 모델은 있지만 라우터 없음
- [ ] 어드민에서 리뷰 수정/삭제 시 `spots.rating_avg`/`review_count` 동기화
- [ ] Array 컬럼(`themes`, `amenities` 등) 어드민 편집 UI 개선

### 중기

- [ ] 로그인/회원가입 rate limiting (brute force 방어)
- [ ] JWT Refresh Token 도입 (현재 24시간 단일 토큰)
- [ ] 공공 데이터 CSV bulk import 기능 (spots 데이터 대량 등록)
- [ ] PostGIS 연동 (`geom` 컬럼 추가, 반경 검색)
- [ ] 스팟 이미지 업로드 (S3 or Lightsail Object Storage)

### 알려진 이슈 / 주의사항

- Google OAuth 유저의 `hashed_password = ""` — 보안 홀은 아니나 코드상 명시적이지 않음
- `spots`의 Array 컬럼은 어드민 form에서 편집 불가 (sqladmin 한계)
- `ADMIN_PASSWORD`가 `.env.local`에 `admin1234`로 기록됨 — prod 배포 전 반드시 변경
- `ACCESS_TOKEN_EXPIRE_MINUTES = 1440` (24시간) — 운영 시 단축 + refresh token 도입 권장
