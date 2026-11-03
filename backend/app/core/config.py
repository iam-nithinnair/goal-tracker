from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "local"
    supabase_url: str = "http://127.0.0.1:54321"
    supabase_service_role_key: str = ""
    # Only used by tests, which sign real users in through Supabase Auth.
    supabase_anon_key: str = ""
    # Only needed for projects that still sign tokens with a shared HS256 secret.
    # Newer projects use asymmetric keys, verified through the JWKS endpoint.
    supabase_jwt_secret: str | None = None
    jwt_audience: str = "authenticated"
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def jwks_url(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
