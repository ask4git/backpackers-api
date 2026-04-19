# Spots 검색 API 구현 보고서

작성일: 2026-04-19

---

## 1. 개요

캠핑장(Spot) 검색 기능을 구현했습니다. 로그인 없이 누구나 사용할 수 있으며, 이름/주소 검색·지역 필터·편의시설 필터를 하나의 엔드포인트에서 조합하여 사용할 수 있습니다.

---

## 2. 구현된 엔드포인트

### 2-1. `GET /spots` — 캠핑장 검색·필터·목록

모든 검색/필터 조건을 단일 엔드포인트에서 처리합니다. 조건은 독립적으로 또는 조합하여 사용 가능합니다.

**쿼리 파라미터**

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `q` | string | - | 캠핑장 이름 또는 주소 검색 (ILIKE) |
| `province` | string | - | 도/특별시/광역시 (1depth 지역 필터) |
| `city` | string | - | 시/군/구 (2depth 지역 필터) |
| `amenities` | string[] | [] | 편의시설 필터 (복수 선택, **AND 조건**) |
| `sort` | string | `rating` | 정렬 기준: `rating` \| `review_count` \| `name` |
| `page` | int | 1 | 페이지 번호 (1 이상) |
| `limit` | int | 20 | 페이지당 항목 수 (1~100) |

**응답 예시**

```json
{
  "items": [
    {
      "uid": "...",
      "title": "설악산 오토캠핑장",
      "address": "강원특별자치도 속초시 설악산로 1",
      "region_province": "강원특별자치도",
      "region_city": "속초시",
      "latitude": 38.12,
      "longitude": 128.46,
      "category": ["일반야영장"],
      "amenities": ["주차장", "화장실", "샤워장"],
      "themes": ["숲속"],
      "is_pet_allowed": true,
      "is_fee_required": true,
      "rating_avg": 4.5,
      "review_count": 12
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 20,
  "total_pages": 8
}
```

**사용 예시**

```
# 이름 검색
GET /spots?q=설악

# 지역 2depth 필터
GET /spots?province=강원특별자치도&city=속초시

# 편의시설 AND 필터 (주차장·샤워장 둘 다 있는 캠핑장)
GET /spots?amenities=주차장&amenities=샤워장

# 조합 (강원도, 샤워장 있는 곳, 별점 높은 순)
GET /spots?province=강원특별자치도&amenities=샤워장&sort=rating

# 페이지네이션
GET /spots?page=2&limit=10
```

---

### 2-2. `GET /spots/regions` — 지역 목록

지역 필터 드롭다운 구성용 엔드포인트입니다. DB에 실제 존재하는 province → cities 계층 구조를 반환합니다.

**응답 예시**

```json
{
  "regions": [
    {
      "province": "강원특별자치도",
      "cities": ["강릉시", "속초시", "춘천시"]
    },
    {
      "province": "제주특별자치도",
      "cities": ["서귀포시", "제주시"]
    }
  ]
}
```

> **프론트엔드 활용**: 앱 시작 시 한 번 요청하여 캐싱 → province 선택 시 해당 cities만 표시하는 cascading 드롭다운 구현.

---

### 2-3. `GET /spots/{spot_uid}` — 캠핑장 상세 조회

목록(SpotSummary)보다 많은 필드를 포함합니다.

**추가 필드**: `description`, `tagline`, `features`, `phone`, `website_url`, `booking_url`, `nearby_facilities`, `fire_pit_type`, `camp_sight_type`, `has_equipment_rental`, `total_area_m2`, `unit_count`, `created_at`, `updated_at`

**에러**: 존재하지 않는 uid → `404 존재하지 않는 캠핑장입니다.`

---

## 3. 생성된 파일

```
app/
├── schemas/spot.py        # SpotSummary, SpotDetail, SpotSearchResponse, RegionListResponse
├── crud/spot.py           # search_spots, get_spot_by_uid, get_regions
└── routers/spots.py       # GET /spots, /spots/regions, /spots/{uid}

tests/
└── test_spots.py          # 38개 테스트

docs/
└── openapi.json           # SpotSummary, SpotDetail, SpotSearchResponse, RegionListResponse 스키마
                           # /spots/regions 경로 추가 (기존 내용 유지)
```

---

## 4. 쿼리 최적화

### 현재 활용 중인 인덱스 (기존 모델에 선언됨)

| 컬럼 | 인덱스 | 필터 용도 |
|---|---|---|
| `title` | B-tree | `q` 이름 검색 (ILIKE) |
| `region_province` | B-tree | `province` 필터 |
| `region_city` | B-tree | `city` 필터 |
| `rating_avg` | B-tree | `sort=rating` 정렬 |

### 편의시설 필터 (`@>` 연산자)

PostgreSQL ARRAY의 `@>` (contains all) 연산자를 사용합니다.

```sql
-- amenities=주차장&amenities=샤워장 요청 시 생성되는 조건
WHERE amenities @> ARRAY['주차장', '샤워장']
```

> **최적화 여지**: `amenities` 컬럼에 GIN 인덱스를 추가하면 `@>` 연산 성능이 크게 향상됩니다.
> ```sql
> CREATE INDEX ix_spots_amenities ON spots USING GIN (amenities);
> ```

### `/spots/regions`

`DISTINCT` 쿼리 1회로 전체 지역 트리를 구성합니다. 데이터 변경이 거의 없으므로 응용 레이어 캐싱(Redis TTL 1시간 등) 적용 시 DB 부하를 줄일 수 있습니다.

---

## 5. 테스트 결과

```
64 passed, 0 failed  (기존 26개 + 신규 38개)
```

### 신규 테스트 분류 (38개)

| 분류 | 테스트 수 |
|---|---|
| `GET /spots` 기본 (전체 조회, 스키마, 빈 DB) | 3 |
| 이름/주소 검색 (`q` 파라미터) | 4 |
| 지역 필터 (province, city, 조합) | 4 |
| 편의시설 필터 (단일, AND, 불일치) | 4 |
| 복합 필터 조합 | 2 |
| 정렬 (rating, review_count, name) | 4 |
| 페이지네이션 (limit, page, 범위 초과, 유효성) | 5 |
| `GET /spots/regions` | 6 |
| `GET /spots/{uid}` 상세 조회 | 6 |
| **합계** | **38** |

---

## 6. 아키텍처 레이어 준수

```
routers/spots.py  →  HTTP 요청/응답, 파라미터 파싱, 의존성 주입만
crud/spot.py      →  DB 쿼리 로직만 (SQLAlchemy, 필터 조합, 정렬)
schemas/spot.py   →  Pydantic 입출력 모델
```

비즈니스 로직 없이 `routers → crud → models` 의존 구조를 유지했습니다.

---

## 7. 인증

세 엔드포인트 모두 **인증 불필요** (공개 API)입니다.
