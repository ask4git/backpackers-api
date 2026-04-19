from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin
from sqladmin.authentication import AuthenticationBackend

from app.admin import SpotAdmin, SpotBusinessInfoAdmin, SpotReviewAdmin, UserAdmin
from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal
from app.routers import auth, reviews

app = FastAPI(
    title="Backpackers API",
    description="국립공원·캠핑장 정보 플랫폼 API",
    version="0.1.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(reviews.router)


# ── 어드민 패널 ───────────────────────────────────────────────────────────────


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        if not settings.ADMIN_PASSWORD:
            return False
        form = await request.form()
        if (
            form.get("username") == settings.ADMIN_USERNAME
            and form.get("password") == settings.ADMIN_PASSWORD
        ):
            request.session.update({"admin": "authenticated"})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        return request.session.get("admin") == "authenticated"


admin = Admin(
    app,
    engine,
    session_maker=AsyncSessionLocal,
    authentication_backend=AdminAuth(secret_key=settings.SECRET_KEY),
    title="Backpackers 어드민",
)
admin.add_view(SpotAdmin)
admin.add_view(SpotBusinessInfoAdmin)
admin.add_view(SpotReviewAdmin)
admin.add_view(UserAdmin)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
