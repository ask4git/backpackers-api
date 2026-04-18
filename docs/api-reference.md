# Backpackers API Reference

**Base URL:** `https://<lightsail-domain>`

---

## 인증

JWT Bearer Token 방식 사용.
로그인/소셜 로그인 후 받은 `access_token`을 헤더에 포함:

```
Authorization: Bearer <access_token>
```

---

## Health

### GET /health
서버 상태 확인

**응답**
```json
{ "status": "ok", "environment": "prod" }
```

---

## Auth

### POST /auth/register
이메일 회원가입

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "string",
  "name": "홍길동"
}
```

**Response** `201`
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "홍길동",
    "created_at": "2026-04-16T00:00:00Z"
  }
}
```

---

### POST /auth/login
이메일 로그인

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "string"
}
```

**Response** `200` — 회원가입과 동일

---

### POST /auth/google/verify
Google 소셜 로그인. 프론트엔드가 Google SDK로 획득한 ID Token을 전달하면 백엔드에서 검증 후 앱 토큰 발급.

**Flow**
1. 프론트엔드가 Google Sign-In SDK로 로그인 → Google ID Token 획득
2. 해당 ID Token을 이 엔드포인트에 전달
3. 백엔드 검증 후 `access_token` 반환

**Request Body**
```json
{
  "id_token": "<Google ID Token>"
}
```

**Response** `200` — 회원가입과 동일 (신규 유저면 자동 생성)

**에러**
- `400` — 유효하지 않은 Google 토큰 또는 이메일 없음

---

## Camping Spots

### GET /spots
캠핑장 목록 조회 (페이지네이션 + 필터)

**Query Params**
| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `q` | string | - | 이름·설명·태그 검색 |
| `region` | RegionEnum | - | 지역 필터 |
| `amenities` | AmenityEnum[] | - | 편의시설 필터 (복수 선택) |
| `page` | int | 1 | 페이지 번호 |
| `limit` | int | 20 | 페이지당 개수 (최대 100) |

**RegionEnum 값**
`서울` `경기` `강원` `충북` `충남` `전북` `전남` `경북` `경남` `제주`

**AmenityEnum 값**
`toilet` `parking` `water` `shower` `fire_pit` `trash`

**Response** `200`
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "북한산 캠핑장",
      "location": {
        "lat": 37.123,
        "lng": 126.456,
        "address": "서울시 은평구 ...",
        "region": "서울"
      },
      "amenities": ["toilet", "parking"],
      "tags": ["가족", "초보"],
      "rating": 4.5,
      "review_count": 120,
      "status": "verified",
      "thumbnail_image": "https://..."
    }
  ],
  "total": 100,
  "page": 1,
  "limit": 20,
  "total_pages": 5
}
```

---

### GET /spots/{spot_id}
캠핑장 상세 조회

**Path Params**
| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `spot_id` | UUID | 캠핑장 ID |

**Response** `200`
```json
{
  "id": "uuid",
  "name": "북한산 캠핑장",
  "description": "서울 근교 최고의 캠핑장",
  "location": {
    "lat": 37.123,
    "lng": 126.456,
    "address": "서울시 은평구 ...",
    "region": "서울"
  },
  "amenities": ["toilet", "parking", "water"],
  "tags": ["가족", "초보"],
  "images": ["https://..."],
  "source": "public_data",
  "status": "verified",
  "rating": 4.5,
  "review_count": 120,
  "created_at": "2026-04-16T00:00:00Z",
  "updated_at": "2026-04-16T00:00:00Z"
}
```

**에러**
- `404` — 캠핑장을 찾을 수 없습니다

---

### POST /spots/report
캠핑장 제보 (로그인 필요)

**Headers** `Authorization: Bearer <token>`

**Request Body**
```json
{
  "name": "새로운 캠핑장",
  "description": "설명",
  "lat": 37.123,
  "lng": 126.456,
  "address": "주소",
  "amenities": ["toilet", "parking"],
  "images": ["https://..."],
  "reporter_contact": "010-0000-0000"
}
```

**Response** `201`
```json
{
  "id": "uuid",
  "name": "새로운 캠핑장",
  "description": "설명",
  "lat": 37.123,
  "lng": 126.456,
  "address": "주소",
  "amenities": ["toilet", "parking"],
  "images": ["https://..."],
  "reporter_contact": "010-0000-0000",
  "status": "pending",
  "created_at": "2026-04-16T00:00:00Z"
}
```

**에러**
- `401` — 인증 필요

---

## 에러 형식

모든 에러는 아래 형식으로 반환됩니다:
```json
{
  "detail": "에러 메시지"
}
```

| 코드 | 의미 |
|------|------|
| 400 | 잘못된 요청 |
| 401 | 인증 실패 / 토큰 없음 |
| 404 | 리소스 없음 |
| 500 | 서버 오류 |
