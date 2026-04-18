# ERD (Entity Relationship Diagram)

> SQLAlchemy 모델 기준으로 작성. 스키마 변경 시 이 파일을 함께 업데이트할 것.

```mermaid
erDiagram
    users {
        UUID    id              PK
        String  email           "unique, indexed"
        String  hashed_password
        String  name
        DateTime created_at
        DateTime updated_at
    }

    spots {
        UUID    uid              PK
        String  title            "indexed"
        String  address          "nullable"
        String  address_detail   "nullable"
        String  region_province  "nullable, indexed"
        String  region_city      "nullable, indexed"
        String  postal_code      "nullable"
        String  phone            "nullable"
        String  description      "nullable"
        String  tagline          "nullable"
        Float   latitude         "nullable"
        Float   longitude        "nullable"
        Float   altitude         "nullable"
        Integer unit_count       "nullable"
        Boolean is_fee_required  "nullable"
        Boolean is_pet_allowed   "nullable"
        String  pet_policy       "nullable"
        Boolean has_equipment_rental "nullable"
        Array   themes           "nullable"
        String  fire_pit_type    "nullable"
        Array   amenities        "nullable"
        Array   nearby_facilities "nullable"
        String  camp_sight_type  "nullable"
        DateTime created_at
        DateTime updated_at
    }

    spot_business_info {
        UUID    uid                       PK
        UUID    spot_uid                  FK "indexed"
        String  business_reg_no           "nullable"
        String  tourism_business_reg_no   "nullable"
        String  business_type             "nullable"
        String  operation_type            "nullable"
        String  operating_agency          "nullable"
        String  operating_status          "nullable, indexed"
        Integer national_park_no          "nullable"
        String  national_park_office_code "nullable"
        String  national_park_serial_no   "nullable"
        String  national_park_category_code "nullable"
        Date    licensed_at               "nullable"
        DateTime created_at
        DateTime updated_at
    }

    spots ||--|| spot_business_info : "business_info"
```

## 테이블 설명

| 테이블 | 설명 |
|---|---|
| `users` | 회원 계정 (이메일/패스워드 인증) |
| `spots` | 국립공원 등 공공 raw 데이터 기반 스팟 |
| `spot_business_info` | spots의 사업자/인허가 정보 (1:1) |
