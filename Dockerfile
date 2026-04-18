FROM python:3.12-slim

# uv 버전 고정으로 재현 가능한 빌드 보장
COPY --from=ghcr.io/astral-sh/uv:0.5.26 /uv /usr/local/bin/uv

WORKDIR /app

# 의존성 먼저 설치 (레이어 캐시 활용)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 앱 코드 복사
COPY . .

RUN chmod +x scripts/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["scripts/entrypoint.sh"]
