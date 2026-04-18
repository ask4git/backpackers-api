import os
from typing import Literal

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ENV_FILE 이름으로 환경 자동 추론
# 예: ENV_FILE=.env.local → ENVIRONMENT=local
_ENV_FILE = os.environ.get("ENV_FILE", ".env.local")
_INFERRED_ENVIRONMENT = next(
    (env for env in ("local", "devel", "prod") if _ENV_FILE.endswith(f".{env}")),
    "local",
)


class Settings(BaseSettings):
    ENVIRONMENT: Literal["local", "devel", "prod"] = _INFERRED_ENVIRONMENT

    # ── 데이터베이스 ───────────────────────────────────────────────────────────
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # ── 보안 ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24시간

    # ── Google OAuth ──────────────────────────────────────────────────────────
    # ID Token 검증에는 CLIENT_ID만 필요 (프론트엔드가 Google과 직접 인증)
    GOOGLE_CLIENT_ID: str = ""

    # ── CORS ──────────────────────────────────────────────────────────────────
    # 쉼표 구분 문자열로 주입받아 리스트로 변환
    # 예: "https://app.example.com,https://www.example.com"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_in_production(cls, v: str, info) -> str:
        environment = info.data.get("ENVIRONMENT", "local")
        if environment == "prod" and "*" in v:
            raise ValueError(
                "CORS_ORIGINS에 '*'을 사용할 수 없습니다. "
                "실제 프론트엔드 도메인을 명시하세요."
            )
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "prod"

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
