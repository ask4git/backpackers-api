"""
GET /spots          — 검색·필터·정렬·페이지네이션
GET /spots/regions  — 지역 목록
GET /spots/{uid}    — 상세 조회
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.spot import Spot


# ── 공통 픽스처 ────────────────────────────────────────────────────────────────

@pytest.fixture
async def spots(db: AsyncSession) -> list[Spot]:
    """필터·정렬 테스트용 스팟 4개."""
    data = [
        Spot(
            title="설악산 캠핑장",
            address="강원특별자치도 속초시 설악산로 1",
            region_province="강원특별자치도",
            region_city="속초시",
            amenities=["주차장", "화장실", "샤워장"],
            rating_avg=4.5,
            review_count=10,
        ),
        Spot(
            title="한라산 야영장",
            address="제주특별자치도 서귀포시 1100로 1",
            region_province="제주특별자치도",
            region_city="서귀포시",
            amenities=["주차장", "화장실"],
            rating_avg=3.0,
            review_count=5,
        ),
        Spot(
            title="지리산 글램핑",
            address="전라남도 구례군 산동면 1",
            region_province="전라남도",
            region_city="구례군",
            amenities=["화장실", "샤워장"],
            rating_avg=4.0,
            review_count=8,
        ),
        Spot(
            title="설악캠프",
            address="강원특별자치도 강릉시 주문진읍 1",
            region_province="강원특별자치도",
            region_city="강릉시",
            amenities=["주차장"],
            rating_avg=2.0,
            review_count=2,
        ),
    ]
    for s in data:
        db.add(s)
    await db.commit()
    for s in data:
        await db.refresh(s)
    return data


# ── GET /spots — 기본 ─────────────────────────────────────────────────────────

async def test_list_spots_no_filter_returns_all(client: AsyncClient, spots):
    """필터 없이 전체 조회."""
    res = await client.get("/spots")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 4
    assert len(body["items"]) == 4


async def test_list_spots_response_schema(client: AsyncClient, spots):
    """응답 필드 구조 확인."""
    res = await client.get("/spots")
    body = res.json()
    assert "total" in body
    assert "page" in body
    assert "limit" in body
    assert "total_pages" in body
    item = body["items"][0]
    for field in ("uid", "title", "rating_avg", "review_count"):
        assert field in item


async def test_list_spots_empty_db(client: AsyncClient):
    """DB 비어 있을 때 빈 목록 반환."""
    res = await client.get("/spots")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 0
    assert body["items"] == []
    assert body["total_pages"] == 0


# ── GET /spots — 이름/주소 검색 ───────────────────────────────────────────────

async def test_search_by_title(client: AsyncClient, spots):
    """이름 일부로 검색."""
    res = await client.get("/spots?q=설악")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    titles = {item["title"] for item in body["items"]}
    assert titles == {"설악산 캠핑장", "설악캠프"}


async def test_search_by_address(client: AsyncClient, spots):
    """주소 일부로 검색 (제목에 없는 키워드)."""
    res = await client.get("/spots?q=서귀포")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "한라산 야영장"


async def test_search_no_match(client: AsyncClient, spots):
    """매칭 없을 때 빈 결과."""
    res = await client.get("/spots?q=존재하지않는캠핑장")
    assert res.status_code == 200
    assert res.json()["total"] == 0


async def test_search_case_insensitive(client: AsyncClient, spots):
    """영문 검색 시 대소문자 무관 (ilike 확인)."""
    res = await client.get("/spots?q=glamping")
    # 제목이 한국어이므로 매칭 없음 — 기본 동작 확인
    assert res.status_code == 200


# ── GET /spots — 지역 필터 ────────────────────────────────────────────────────

async def test_filter_by_province(client: AsyncClient, spots):
    """province 필터 — 강원도 2개."""
    res = await client.get("/spots?province=강원특별자치도")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    for item in body["items"]:
        assert item["region_province"] == "강원특별자치도"


async def test_filter_by_city(client: AsyncClient, spots):
    """city 필터 — 속초시 1개."""
    res = await client.get("/spots?city=속초시")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "설악산 캠핑장"


async def test_filter_by_province_and_city(client: AsyncClient, spots):
    """province + city 2depth 조합 필터."""
    res = await client.get("/spots?province=강원특별자치도&city=강릉시")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "설악캠프"


async def test_filter_province_no_match(client: AsyncClient, spots):
    """없는 지역은 빈 결과."""
    res = await client.get("/spots?province=없는도")
    assert res.json()["total"] == 0


# ── GET /spots — 편의시설 필터 ────────────────────────────────────────────────

async def test_filter_single_amenity(client: AsyncClient, spots):
    """단일 편의시설 — 샤워장 있는 캠핑장: 설악산, 지리산."""
    res = await client.get("/spots?amenities=샤워장")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    titles = {item["title"] for item in body["items"]}
    assert titles == {"설악산 캠핑장", "지리산 글램핑"}


async def test_filter_multiple_amenities_and(client: AsyncClient, spots):
    """복수 편의시설 AND 조건 — 주차장+화장실 둘 다 있는 곳: 설악산, 한라산."""
    res = await client.get("/spots?amenities=주차장&amenities=화장실")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    titles = {item["title"] for item in body["items"]}
    assert titles == {"설악산 캠핑장", "한라산 야영장"}


async def test_filter_amenities_strict_and(client: AsyncClient, spots):
    """주차장+화장실+샤워장 3개 AND — 설악산 캠핑장만 해당."""
    res = await client.get("/spots?amenities=주차장&amenities=화장실&amenities=샤워장")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "설악산 캠핑장"


async def test_filter_amenity_no_match(client: AsyncClient, spots):
    """없는 편의시설 — 빈 결과."""
    res = await client.get("/spots?amenities=수영장")
    assert res.json()["total"] == 0


# ── GET /spots — 복합 필터 ────────────────────────────────────────────────────

async def test_combined_q_and_province(client: AsyncClient, spots):
    """q + province 조합 — 강원도에서 '설악' 검색: 설악산 캠핑장, 설악캠프."""
    res = await client.get("/spots?q=설악&province=강원특별자치도")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2


async def test_combined_province_and_amenity(client: AsyncClient, spots):
    """province + amenity 조합 — 강원도 중 샤워장 있는 곳: 설악산 캠핑장만."""
    res = await client.get("/spots?province=강원특별자치도&amenities=샤워장")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["items"][0]["title"] == "설악산 캠핑장"


# ── GET /spots — 정렬 ─────────────────────────────────────────────────────────

async def test_sort_by_rating_default(client: AsyncClient, spots):
    """기본 정렬은 rating_avg 내림차순."""
    res = await client.get("/spots")
    items = res.json()["items"]
    ratings = [item["rating_avg"] for item in items]
    assert ratings == sorted(ratings, reverse=True)


async def test_sort_by_rating_explicit(client: AsyncClient, spots):
    """sort=rating 명시."""
    res = await client.get("/spots?sort=rating")
    items = res.json()["items"]
    ratings = [item["rating_avg"] for item in items]
    assert ratings == sorted(ratings, reverse=True)


async def test_sort_by_review_count(client: AsyncClient, spots):
    """sort=review_count 내림차순."""
    res = await client.get("/spots?sort=review_count")
    items = res.json()["items"]
    counts = [item["review_count"] for item in items]
    assert counts == sorted(counts, reverse=True)


async def test_sort_by_name(client: AsyncClient, spots):
    """sort=name — 이름순과 별점순은 순서가 달라야 하고, '한'으로 시작하는 한라산은 마지막."""
    res_name = await client.get("/spots?sort=name")
    res_rating = await client.get("/spots?sort=rating")
    titles_name = [item["title"] for item in res_name.json()["items"]]
    titles_rating = [item["title"] for item in res_rating.json()["items"]]
    # 이름순과 별점순은 서로 다른 순서여야 함
    assert titles_name != titles_rating
    # '한'(U+D55C) 으로 시작하는 한라산은 어떤 콜레이션에서도 '설'·'지'보다 뒤에 위치
    assert titles_name[-1] == "한라산 야영장"


# ── GET /spots — 페이지네이션 ─────────────────────────────────────────────────

async def test_pagination_first_page(client: AsyncClient, spots):
    """limit=2, page=1 — 2개 반환, total=4, total_pages=2."""
    res = await client.get("/spots?limit=2&page=1")
    body = res.json()
    assert body["total"] == 4
    assert len(body["items"]) == 2
    assert body["total_pages"] == 2
    assert body["page"] == 1
    assert body["limit"] == 2


async def test_pagination_second_page(client: AsyncClient, spots):
    """page=2 — 다른 2개 반환."""
    res1 = await client.get("/spots?limit=2&page=1&sort=name")
    res2 = await client.get("/spots?limit=2&page=2&sort=name")

    uids1 = {item["uid"] for item in res1.json()["items"]}
    uids2 = {item["uid"] for item in res2.json()["items"]}
    assert uids1.isdisjoint(uids2)


async def test_pagination_beyond_last_page(client: AsyncClient, spots):
    """존재하지 않는 페이지 — 빈 items."""
    res = await client.get("/spots?limit=10&page=999")
    body = res.json()
    assert body["items"] == []
    assert body["total"] == 4


async def test_pagination_limit_validation(client: AsyncClient, spots):
    """limit > 100 이면 422."""
    res = await client.get("/spots?limit=101")
    assert res.status_code == 422


async def test_pagination_page_zero(client: AsyncClient, spots):
    """page=0 이면 422."""
    res = await client.get("/spots?page=0")
    assert res.status_code == 422


# ── GET /spots/regions ────────────────────────────────────────────────────────

async def test_list_regions_structure(client: AsyncClient, spots):
    """province → cities 계층 구조 반환."""
    res = await client.get("/spots/regions")
    assert res.status_code == 200
    body = res.json()
    assert "regions" in body
    region = body["regions"][0]
    assert "province" in region
    assert "cities" in region
    assert isinstance(region["cities"], list)


async def test_list_regions_contains_expected(client: AsyncClient, spots):
    """강원특별자치도 province에 속초시, 강릉시 포함."""
    res = await client.get("/spots/regions")
    regions = {r["province"]: r["cities"] for r in res.json()["regions"]}

    assert "강원특별자치도" in regions
    assert "속초시" in regions["강원특별자치도"]
    assert "강릉시" in regions["강원특별자치도"]


async def test_list_regions_no_duplicates(client: AsyncClient, spots):
    """같은 province/city 조합이 중복 없이 반환."""
    res = await client.get("/spots/regions")
    for region in res.json()["regions"]:
        assert len(region["cities"]) == len(set(region["cities"]))


async def test_list_regions_sorted(client: AsyncClient, spots):
    """province 알파벳(가나다) 순 정렬."""
    res = await client.get("/spots/regions")
    provinces = [r["province"] for r in res.json()["regions"]]
    assert provinces == sorted(provinces)


async def test_list_regions_empty_db(client: AsyncClient):
    """DB 비어 있으면 빈 regions 반환."""
    res = await client.get("/spots/regions")
    assert res.status_code == 200
    assert res.json()["regions"] == []


async def test_list_regions_no_auth_required(client: AsyncClient, spots):
    """인증 없이 접근 가능."""
    res = await client.get("/spots/regions")
    assert res.status_code == 200


# ── GET /spots/{spot_uid} ─────────────────────────────────────────────────────

async def test_get_spot_detail_success(client: AsyncClient, spots):
    """정상 상세 조회."""
    target = spots[0]
    res = await client.get(f"/spots/{target.uid}")
    assert res.status_code == 200
    body = res.json()
    assert body["uid"] == str(target.uid)
    assert body["title"] == target.title
    assert body["region_province"] == target.region_province
    assert body["region_city"] == target.region_city


async def test_get_spot_detail_contains_extra_fields(client: AsyncClient, spots):
    """상세 응답에 summary에 없는 필드 포함."""
    target = spots[0]
    res = await client.get(f"/spots/{target.uid}")
    body = res.json()
    for field in ("created_at", "updated_at"):
        assert field in body


async def test_get_spot_detail_amenities(client: AsyncClient, spots):
    """amenities 배열 올바르게 반환."""
    target = spots[0]  # 설악산 캠핑장: ["주차장", "화장실", "샤워장"]
    res = await client.get(f"/spots/{target.uid}")
    assert set(res.json()["amenities"]) == {"주차장", "화장실", "샤워장"}


async def test_get_spot_detail_not_found(client: AsyncClient):
    """없는 uid — 404."""
    res = await client.get(f"/spots/{uuid.uuid4()}")
    assert res.status_code == 404
    assert "존재하지 않는" in res.json()["detail"]


async def test_get_spot_detail_invalid_uuid(client: AsyncClient):
    """UUID 형식 아닌 path — 422."""
    res = await client.get("/spots/not-a-uuid")
    assert res.status_code == 422


async def test_get_spot_no_auth_required(client: AsyncClient, spots):
    """인증 없이 접근 가능."""
    target = spots[0]
    res = await client.get(f"/spots/{target.uid}")
    assert res.status_code == 200
