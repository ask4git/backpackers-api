"""
POST /spots/{spot_uid}/reviews
GET  /spots/{spot_uid}/reviews
"""
import uuid

from httpx import AsyncClient


# ── 리뷰 작성 (POST) ───────────────────────────────────────────────────────────

async def test_write_review_success(client: AsyncClient, spot, auth_headers, db):
    """정상 리뷰 작성 후 spot.rating_avg가 갱신되는지 확인."""
    from sqlalchemy import select
    from app.models.spot import Spot

    res = await client.post(
        f"/spots/{spot.uid}/reviews",
        json={"rating": 4.5, "content": "좋아요!"},
        headers=auth_headers,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["rating"] == 4.5
    assert body["content"] == "좋아요!"
    assert body["spot_uid"] == str(spot.uid)

    # spots.rating_avg 캐시 갱신 확인
    await db.refresh(spot)
    result = await db.execute(select(Spot).where(Spot.uid == spot.uid))
    updated_spot = result.scalar_one()
    assert updated_spot.rating_avg == 4.5
    assert updated_spot.review_count == 1


async def test_write_review_no_content(client: AsyncClient, spot, auth_headers):
    """content 없이 rating만으로 리뷰 작성 가능."""
    res = await client.post(
        f"/spots/{spot.uid}/reviews",
        json={"rating": 3.0},
        headers=auth_headers,
    )
    assert res.status_code == 201
    assert res.json()["content"] is None


async def test_write_review_no_auth(client: AsyncClient, spot):
    """토큰 없이 요청 시 401."""
    res = await client.post(
        f"/spots/{spot.uid}/reviews",
        json={"rating": 4.0, "content": "인증 없음"},
    )
    assert res.status_code == 401


async def test_write_review_invalid_token(client: AsyncClient, spot):
    """변조된 토큰으로 요청 시 401."""
    res = await client.post(
        f"/spots/{spot.uid}/reviews",
        json={"rating": 4.0},
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert res.status_code == 401


async def test_write_review_duplicate(client: AsyncClient, spot, auth_headers):
    """같은 스팟에 두 번 리뷰 작성 시 409."""
    payload = {"rating": 4.0, "content": "첫 리뷰"}
    await client.post(f"/spots/{spot.uid}/reviews", json=payload, headers=auth_headers)

    res = await client.post(f"/spots/{spot.uid}/reviews", json=payload, headers=auth_headers)
    assert res.status_code == 409
    assert "이미" in res.json()["detail"]


async def test_write_review_rating_too_high(client: AsyncClient, spot, auth_headers):
    """rating > 5 이면 422 (Pydantic 검증)."""
    res = await client.post(
        f"/spots/{spot.uid}/reviews",
        json={"rating": 5.1},
        headers=auth_headers,
    )
    assert res.status_code == 422


async def test_write_review_rating_negative(client: AsyncClient, spot, auth_headers):
    """rating < 0 이면 422."""
    res = await client.post(
        f"/spots/{spot.uid}/reviews",
        json={"rating": -0.1},
        headers=auth_headers,
    )
    assert res.status_code == 422


async def test_write_review_invalid_spot(client: AsyncClient, auth_headers):
    """존재하지 않는 spot_uid이면 404."""
    fake_uid = uuid.uuid4()
    res = await client.post(
        f"/spots/{fake_uid}/reviews",
        json={"rating": 4.0},
        headers=auth_headers,
    )
    assert res.status_code == 404


# ── 리뷰 목록 조회 (GET) ───────────────────────────────────────────────────────

async def test_list_reviews_empty(client: AsyncClient, spot):
    """리뷰 없는 스팟 조회 시 빈 목록과 0.0 평균 반환."""
    res = await client.get(f"/spots/{spot.uid}/reviews")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 0
    assert body["items"] == []
    assert body["rating_avg"] == 0.0


async def test_list_reviews_with_data(client: AsyncClient, spot, auth_headers, another_auth_headers):
    """리뷰 2개 작성 후 목록과 평균 별점이 정확한지 확인."""
    await client.post(f"/spots/{spot.uid}/reviews", json={"rating": 4.0, "content": "좋음"}, headers=auth_headers)
    await client.post(f"/spots/{spot.uid}/reviews", json={"rating": 2.0, "content": "별로"}, headers=another_auth_headers)

    res = await client.get(f"/spots/{spot.uid}/reviews")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 2
    assert len(body["items"]) == 2
    assert body["rating_avg"] == 3.0  # (4.0 + 2.0) / 2


async def test_list_reviews_rating_avg_accuracy(client: AsyncClient, spot, auth_headers, another_auth_headers):
    """평균 별점 소수점 정확도 확인."""
    await client.post(f"/spots/{spot.uid}/reviews", json={"rating": 5.0}, headers=auth_headers)
    await client.post(f"/spots/{spot.uid}/reviews", json={"rating": 4.0}, headers=another_auth_headers)

    res = await client.get(f"/spots/{spot.uid}/reviews")
    assert res.json()["rating_avg"] == 4.5


async def test_list_reviews_ordered_by_latest(client: AsyncClient, spot, auth_headers, another_auth_headers):
    """리뷰 목록이 최신순 정렬인지 확인."""
    await client.post(f"/spots/{spot.uid}/reviews", json={"rating": 3.0, "content": "첫번째"}, headers=auth_headers)
    await client.post(f"/spots/{spot.uid}/reviews", json={"rating": 5.0, "content": "두번째"}, headers=another_auth_headers)

    res = await client.get(f"/spots/{spot.uid}/reviews")
    items = res.json()["items"]
    assert items[0]["content"] == "두번째"
    assert items[1]["content"] == "첫번째"


async def test_list_reviews_pagination(client: AsyncClient, spot, auth_headers, another_auth_headers):
    """page, limit 파라미터 동작 확인."""
    await client.post(f"/spots/{spot.uid}/reviews", json={"rating": 4.0}, headers=auth_headers)
    await client.post(f"/spots/{spot.uid}/reviews", json={"rating": 2.0}, headers=another_auth_headers)

    # limit=1이면 1개만 반환, total은 여전히 2
    res = await client.get(f"/spots/{spot.uid}/reviews?page=1&limit=1")
    body = res.json()
    assert body["total"] == 2
    assert len(body["items"]) == 1

    # page=2이면 두 번째 리뷰
    res2 = await client.get(f"/spots/{spot.uid}/reviews?page=2&limit=1")
    body2 = res2.json()
    assert len(body2["items"]) == 1
    assert body2["items"][0]["uid"] != body["items"][0]["uid"]


async def test_list_reviews_invalid_spot(client: AsyncClient):
    """없는 spot_uid이면 빈 목록 반환 (404 아님 — spot 존재 여부 미검증)."""
    fake_uid = uuid.uuid4()
    res = await client.get(f"/spots/{fake_uid}/reviews")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 0
    assert body["rating_avg"] == 0.0
