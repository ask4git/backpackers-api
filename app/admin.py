from sqladmin import ModelView

from app.models.review import SpotReview
from app.models.spot import Spot, SpotBusinessInfo
from app.models.user import User

# Array 타입 컬럼은 sqladmin 기본 편집 UI 미지원 → form에서 제외
_SPOT_ARRAY_COLUMNS = ["themes", "amenities", "nearby_facilities"]


class SpotAdmin(ModelView, model=Spot):
    name = "스팟"
    name_plural = "스팟 목록"
    icon = "fa-solid fa-campground"

    column_list = [
        Spot.uid,
        Spot.title,
        Spot.region_province,
        Spot.region_city,
        Spot.rating_avg,
        Spot.review_count,
        Spot.created_at,
    ]
    column_searchable_list = [Spot.title, Spot.address]
    column_sortable_list = [
        Spot.title,
        Spot.rating_avg,
        Spot.review_count,
        Spot.created_at,
    ]
    column_default_sort = (Spot.created_at, True)

    form_excluded_columns = _SPOT_ARRAY_COLUMNS + ["business_info"]


class SpotBusinessInfoAdmin(ModelView, model=SpotBusinessInfo):
    name = "사업자 정보"
    name_plural = "사업자 정보 목록"
    icon = "fa-solid fa-building"

    column_list = [
        SpotBusinessInfo.uid,
        SpotBusinessInfo.spot_uid,
        SpotBusinessInfo.operating_status,
        SpotBusinessInfo.business_type,
        SpotBusinessInfo.operating_agency,
    ]
    column_searchable_list = [SpotBusinessInfo.operating_agency]
    column_sortable_list = [SpotBusinessInfo.operating_status]

    form_excluded_columns = ["spot"]


class SpotReviewAdmin(ModelView, model=SpotReview):
    name = "리뷰"
    name_plural = "리뷰 목록"
    icon = "fa-solid fa-star"

    column_list = [
        SpotReview.uid,
        SpotReview.spot_uid,
        SpotReview.user_id,
        SpotReview.rating,
        SpotReview.content,
        SpotReview.created_at,
    ]
    column_sortable_list = [SpotReview.rating, SpotReview.created_at]
    column_default_sort = (SpotReview.created_at, True)


class UserAdmin(ModelView, model=User):
    name = "사용자"
    name_plural = "사용자 목록"
    icon = "fa-solid fa-user"

    column_list = [User.id, User.email, User.name, User.created_at]
    column_searchable_list = [User.email, User.name]
    column_sortable_list = [User.created_at]
    column_default_sort = (User.created_at, True)

    # 비밀번호 해시는 폼에서 노출/편집 금지
    form_excluded_columns = ["hashed_password"]
