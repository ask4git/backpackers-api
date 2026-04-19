# 보안 리뷰 및 조치 내역

**작성일**: 2026-04-19
**대상**: backpackers-api 전반 (인증, 배포, 어드민)

---

## 리뷰 항목 및 평가

### (1) JWT 토큰 무효화 불가

| 항목 | 내용 |
|------|------|
| 지적 | `decode_token`이 `exp`만 검증, `iss`/`aud` 클레임 없음. 토큰 블랙리스트/revocation 없음. Refresh Token 미존재 |
| 평가 | **동의 (우선순위: 단기)** |

- `iss`/`aud` 추가는 간단하므로 빠르게 적용 가능
- Refresh Token + 짧은 access token(15~30분) 도입은 사용자 유입 시점에 맞춰 진행
- 토큰 블랙리스트는 Redis 등 인프라가 필요하므로 규모에 맞게 판단

### (2) Rate Limiting 전무

| 항목 | 내용 |
|------|------|
| 지적 | `/auth/login`, `/auth/register`, `/auth/google/verify`에 brute force 방어 없음 |
| 평가 | **동의 (우선순위: 단기)** |

- 애플리케이션 레벨(`slowapi`) 또는 인프라 레벨(CloudFront, ALB) 중 택일
- 현재 인프라 구성(Lightsail) 확인 후 적절한 레이어에서 처리 필요

### (3) 어드민 세션 보안

| 항목 | 내용 |
|------|------|
| 지적 | `SessionMiddleware`가 명시적으로 설정되지 않음. `https_only`, `same_site`, `max_age` 미통제 |
| 평가 | **부분 동의 (우선순위: 나중)** |

- sqladmin이 `AuthenticationBackend(secret_key=...)`를 받으면 내부적으로 `SessionMiddleware`를 자동 등록함
- `main.py:56`에서 `secret_key=settings.SECRET_KEY`로 넘기고 있어 세션 자체는 정상 동작
- 다만 쿠키 속성을 직접 통제하지 못하는 점은 개선 여지 있음

### (4) Google OAuth 유저의 빈 비밀번호 :white_check_mark: 수정 완료

| 항목 | 내용 |
|------|------|
| 지적 | `hashed_password=""`인 유저에게 패스워드 로그인 시도 시 문제 발생 |
| 평가 | **동의 (우선순위: 즉시)** |

**원래 지적의 오류**: `verify_password("anything", "")`가 "운 나쁘게 통과"할 수 있다고 했으나, 실제로는 bcrypt가 빈 문자열을 유효한 해시로 인식하지 못해 **ValueError를 raise**함. 즉 통과가 아니라 **500 에러**가 발생하는 것이 실제 문제.

**수정 내용** (`app/routers/auth.py:36`):

```python
# Before
if not user or not verify_password(data.password, user.hashed_password):

# After
if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
```

`user.hashed_password`가 빈 문자열인 경우 `verify_password`를 호출하지 않고 즉시 401을 반환하여 500 에러를 방지.

### (5) DEPLOY_KEYS에 어드민 인증 정보 누락 :white_check_mark: 수정 완료

| 항목 | 내용 |
|------|------|
| 지적 | `make_deploy_config.py`의 `DEPLOY_KEYS`에 `ADMIN_USERNAME`/`ADMIN_PASSWORD` 미포함 |
| 평가 | **동의 (우선순위: 즉시)** |

- GitHub Actions `deploy.yml`에서는 인라인 Python으로 직접 config를 생성하므로 CI 배포는 문제 없음
- `make deploy`로 수동 배포할 때 어드민 인증 정보가 누락되어 `/admin` 접근 불가 발생 가능

**수정 내용** (`scripts/make_deploy_config.py:25-26`):

```python
DEPLOY_KEYS = [
    # ... 기존 키들 ...
    "CORS_ORIGINS",
    "ENVIRONMENT",
    "ADMIN_USERNAME",   # 추가
    "ADMIN_PASSWORD",   # 추가
]
```

### (6) import_src01.py의 SSL 비활성화

| 항목 | 내용 |
|------|------|
| 지적 | `ssl.CERT_NONE` 사용으로 MITM 취약 |
| 평가 | **과한 지적 (무시)** |

- `.dockerignore`에 `scripts/oneoff/`가 명시적 제외됨
- 1회성 데이터 임포트 스크립트로 배포 이미지에 포함되지 않음

### (7) .dockerignore 관련

| 항목 | 내용 |
|------|------|
| 지적 | `.env*` 패턴이 `.env.local.example` 등을 포함할 수 있음 |
| 평가 | **불필요한 지적 (무시)** |

- `.env*` glob 패턴이 example 파일도 정상적으로 제외함
- 현재 example 파일이 존재하지 않음

---

## 우선순위 요약

| 우선순위 | 항목 | 상태 |
|---------|------|------|
| 즉시 | (4) 빈 비밀번호 가드 | 수정 완료 |
| 즉시 | (5) DEPLOY_KEYS 누락 | 수정 완료 |
| 단기 | (2) Rate limiting | 인프라 구성 확인 후 적용 |
| 단기 | (1) 토큰 만료 단축 + Refresh Token | 사용자 유입 시점에 도입 |
| 나중 | (3) 세션 쿠키 명시적 설정 | sqladmin 기본값으로 동작 중 |
| 무시 | (6) SSL 비활성화 (1회성 스크립트) | 실질적 위험 없음 |
| 무시 | (7) .dockerignore | 실질적 위험 없음 |
