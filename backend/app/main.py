from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.routers import challenges, dashboard, entries, goals, me


def create_app() -> FastAPI:
    settings = get_settings()
    docs = settings.environment != "production"
    app = FastAPI(
        title="Goal Tracker API",
        version="0.1.0",
        docs_url="/docs" if docs else None,
        redoc_url=None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    install_error_handlers(app)

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    for module in (me, challenges, goals, entries, dashboard):
        app.include_router(module.router, prefix="/api/v1")
    return app


app = create_app()
