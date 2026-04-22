"""
현재 환경 설정을 확인하는 진단 스크립트.

사용법:
    ENV_FILE=.env.local uv run python main.py
"""

import sys


def main():
    try:
        from app.core.config import settings
    except Exception as e:
        print(f"[ERROR] 설정 로드 실패: {e}")
        sys.exit(1)

    env_file = __import__("os").environ.get("ENV_FILE", ".env.local")

    print("=" * 40)
    print(f"  Curve API — 환경 설정 확인")
    print("=" * 40)
    print(f"  ENV_FILE     : {env_file}")
    print(f"  ENVIRONMENT  : {settings.ENVIRONMENT}")
    print(f"  DB_HOST      : {settings.DB_HOST}")
    print(f"  DB_PORT      : {settings.DB_PORT}")
    print(f"  DB_USER      : {settings.DB_USER}")
    print(f"  DB_NAME      : {settings.DB_NAME}")
    print(f"  DB_PASSWORD  : {'*' * len(settings.DB_PASSWORD)}")
    print(f"  SECRET_KEY   : {settings.SECRET_KEY[:6]}...")
    print(f"  CORS_ORIGINS : {settings.CORS_ORIGINS}")
    print("=" * 40)


if __name__ == "__main__":
    main()
