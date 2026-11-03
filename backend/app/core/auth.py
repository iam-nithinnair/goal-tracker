"""Verifies the Supabase JWT sent as `Authorization: Bearer <token>`.

Supports both signing modes a Supabase project can use:
  * HS256 with the shared project secret (SUPABASE_JWT_SECRET)
  * asymmetric keys (ES256/RS256), verified via the project's JWKS endpoint
"""

from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from app.core.config import Settings, get_settings
from app.core.errors import ApiError

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    id: str
    email: str | None
    app_role: str = "user"  # 'user' or 'super_admin' (filled in from the profile when needed)


@lru_cache
def _jwks_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_keys=True, lifespan=3600)


def _unauthorized(message: str = "Invalid or missing token") -> ApiError:
    return ApiError(401, "unauthorized", message)


def decode_token(token: str, settings: Settings) -> dict:
    try:
        header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise _unauthorized() from None

    alg = header.get("alg", "")
    try:
        if alg == "HS256":
            if not settings.supabase_jwt_secret:
                raise _unauthorized()
            key = settings.supabase_jwt_secret
            algorithms = ["HS256"]
        elif alg in ("ES256", "RS256"):
            key = _jwks_client(settings.jwks_url).get_signing_key_from_jwt(token).key
            algorithms = [alg]
        else:
            raise _unauthorized()

        return jwt.decode(
            token,
            key,
            algorithms=algorithms,
            audience=settings.jwt_audience,
            options={"require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError:
        raise _unauthorized("Token expired") from None
    except (jwt.PyJWTError, jwt.PyJWKClientError):
        raise _unauthorized() from None


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if creds is None or creds.scheme.lower() != "bearer":
        raise _unauthorized()
    claims = decode_token(creds.credentials, settings)
    if claims.get("role") != "authenticated":
        raise _unauthorized()
    return CurrentUser(id=claims["sub"], email=claims.get("email"))
