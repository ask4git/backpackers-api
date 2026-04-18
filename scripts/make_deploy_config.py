#!/usr/bin/env python3
"""
로컬 .env를 읽어 Lightsail 배포용 containers.json 문자열을 출력합니다.
make deploy LIGHTSAIL_IMAGE=:backpackers-api.backpackers-api.N 에서 호출됩니다.
"""
import json
import sys
from pathlib import Path

from dotenv import dotenv_values


DEPLOY_KEYS = [
    "DATABASE_URL",
    "SECRET_KEY",
    "ALGORITHM",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "GOOGLE_REDIRECT_URI",
    "CORS_ORIGINS",
    "ENVIRONMENT",
]


def main():
    if len(sys.argv) < 2:
        print("Usage: make_deploy_config.py <image_tag>", file=sys.stderr)
        sys.exit(1)

    image_tag = sys.argv[1]
    env_path = Path(__file__).parent.parent / ".env"

    if not env_path.exists():
        print(f"Error: {env_path} not found", file=sys.stderr)
        sys.exit(1)

    env = dotenv_values(env_path)
    environment = {k: str(v) for k, v in env.items() if k in DEPLOY_KEYS and v}

    config = {
        "backpackers-api": {
            "image": image_tag,
            "ports": {"8000": "HTTP"},
            "environment": environment,
        }
    }

    print(json.dumps(config))


if __name__ == "__main__":
    main()
