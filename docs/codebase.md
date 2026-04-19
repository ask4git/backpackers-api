# Backpackers API — 코드베이스 개요

> 최종 업데이트: 2026-04-18

국립공원·캠핑장 정보 플랫폼 POC. FastAPI + PostgreSQL + SQLAlchemy(async) 기반 REST API.

---

## 1. 기술 스택

| 항목 | 내용 |
|------|------|
| 프레임워크 | FastAPI |
| DB | PostgreSQL + SQLAlchemy (async) |
| 마이그레이션 | Alembic |
| 인증 | JWT (python-jose) + Google OAuth |
| 패스워드 해싱 | passlib/bcrypt |
| 어드민 | SQLAdmin |
| 패키지 매니저 | uv |
| 런타임 | Python 3.12+ |

---

## 2. 디렉토리 구조

```
app/
├── main.py             # FastAPI 앱 진입점, 라우터 등록, CORS, 어드민
├── admin.py            # SQLAdmin 뷰 설정
├── dependencies.py     # get_current_user 등 의존성 주입
├── core/
│   ├── config.py       # Pydantic BaseSettings (환경변수 로드)
│   ├── database.py     # AsyncEngine, AsyncSession, Base, get_db
│   └── security.py     # bcrypt 해싱, JWT 생성/검증
├── models/
│   ├── user.py         # User
│   ├── spot.py         # Spot, SpotBusinessInfo
│   └── review.py       # SpotReview
├── schemas/
│   ├── user.py         # UserRegister, UserLogin, TokenResponse, GoogleVerifyRequest
│   └── review.py       # ReviewCreate, ReviewResponse, ReviewListResponse
├── routers/
│   ├── auth.py         # POST /auth/register, /auth/login, /auth/google/verify
│   └── reviews.py      # POST/GET /spots/{spot_uid}/reviews
└── crud/
    ├── user.py         # get_user_by_email, create_user, get_or_create_google_user
    └── review.py       # create_review, get_reviews_by_spot
```

---

## 3. 데이터 모델

### users

| 컬럼 | 타입 | 비고 |
|------|------|------|
| id | UUID | PK |
| email | String | Unique, Index |
| hashed_password | String | bcrypt |
| name | String | |
| created_at / updated_at | DateTime(tz) | |

### spots

| 컬럼 | 타입 | 비고 |
|------|------|------|
| uid | UUID | PK |
| title | String | Index |
| address / address_detail | String | |
| region_province / region_city | String | Index |
| latitude / longitude / altitude | Float | |
| is_fee_required / is_pet_allowed / has_equipment_rental | Boolean | |
| themes / amenities / nearby_facilities | ARRAY(String) | |
| camp_sight_type / fire_pit_type | String | |
| rating_avg | Float | 캐시값 (기본 0.0) |
| review_count | Integer | 캐시값 (기본 0) |
| created_at / updated_at | DateTime(tz) | |

### spot_business_info (spots와 1:1)

| 컬럼 | 타입 | 비고 |
|------|------|------|
| uid | UUID | PK |
| spot_uid | UUID | FK → spots, Index |
| business_reg_no / tourism_business_reg_no | String | |
| business_type / operation_type / operating_agency | String | |
| operating_status | String | Index |
| national_park_no / office_code / serial_no / category_code | String/Int | |
| licensed_at | Date | |

### spot_reviews

| 컬럼 | 타입 | 비고 |
|------|------|------|
| uid | UUID | PK |
| spot_uid | UUID | FK → spots |
| user_id | UUID | FK → users |
| rating | Float | 0~5, Check 제약 |
| content | String | Nullable |
| created_at / updated_at | DateTime(tz) | |

- Unique 제약: `(spot_uid, user_id)` — 사용자 1명은 스팟당 1개 리뷰

---

## 4. API 엔드포인트

### 인증 (`/auth`)

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| POST | `/auth/register` | - | 회원가입 → JWT 발급 |
| POST | `/auth/login` | - | 로그인 → JWT 발급 |
| POST | `/auth/google/verify` | - | Google ID Token 검증 → JWT 발급 |

### 리뷰

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| POST | `/spots/{spot_uid}/reviews` | Bearer | 리뷰 작성 (1인 1리뷰) |
| GET | `/spots/{spot_uid}/reviews` | - | 리뷰 목록 조회 (페이지네이션) |

GET 파라미터: `page` (기본 1), `limit` (기본 20, 최대 100)

### 기타

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/health` | 헬스 체크 |
| GET | `/admin` | SQLAdmin 어드민 패널 |

---

## 5. 주요 흐름

### 인증 흐름

```
POST /auth/login
  → UserLogin 스키마 검증
  → crud.get_user_by_email() + verify_password()
  → create_access_token()
  → TokenResponse (access_token + user)
```

### 리뷰 작성 흐름

```
POST /spots/{spot_uid}/reviews
  → get_current_user() 의존성 (Bearer 토큰 → User)
  → ReviewCreate 스키마 검증 (rating 0~5)
  → crud.create_review()
      → SpotReview INSERT (flush)
      → _refresh_spot_rating() — Spot.rating_avg, review_count 갱신
      → commit
  → ReviewResponse
```

### 리뷰 조회 흐름

```
GET /spots/{spot_uid}/reviews?page=1&limit=20
  → crud.get_reviews_by_spot()
      → COUNT 쿼리 (total)
      → AVG 쿼리 (rating_avg)
      → SELECT + OFFSET/LIMIT (생성일 내림차순)
  → ReviewListResponse (items + total + rating_avg)
```

---

## 6. 핵심 설계 포인트

- **비동기**: SQLAlchemy `AsyncSession` 전면 사용
- **레이어 분리**: routers → crud → models 단방향 의존 (비즈니스 로직은 routers에서 최소화)
- **평점 캐싱**: 리뷰 생성 시 `Spot.rating_avg` / `review_count`를 즉시 갱신해 조회 성능 확보
- **원자성**: 리뷰 INSERT → flush → rating 갱신 → commit 순서로 트랜잭션 안전성 보장
- **환경 분리**: `.env.local` / `.env.devel` / `.env.prod` 각각 별도 관리
- **프로덕션 보안**: Swagger/ReDoc 비활성화, CORS 와일드카드 금지

---

## 7. 환경 설정 (core/config.py)

주요 환경변수:

| 변수 | 기본값 | 설명 |
|------|--------|------|
| DB_HOST / PORT / USER / PASSWORD / NAME | — | PostgreSQL 연결 |
| SECRET_KEY | — | JWT 서명 키 |
| ALGORITHM | HS256 | JWT 알고리즘 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 1440 | 토큰 유효시간 (24h) |
| CORS_ORIGINS | localhost:3000,5173 | 허용 도메인 |
| GOOGLE_CLIENT_ID | — | Google OAuth |
| ADMIN_USERNAME / ADMIN_PASSWORD | admin / (빈값) | SQLAdmin 접근 |

---

## 8. 마이그레이션 히스토리

| 버전 | 날짜 | 내용 |
|------|------|------|
| d3c40504 | 2026-04-16 | 초기 테이블 생성 (users, camping_spots, spot_reports) |
| 5fb2a535 | 2026-04-17 | spots, spot_business_info 테이블 추가 |
| 24da4375 | 2026-04-18 | 레거시 테이블 삭제 (camping_spots, spot_reports) |
| 4e7b6580 | 2026-04-18 | spot_reviews 테이블 추가, Spot에 rating_avg/review_count 컬럼 추가 |
