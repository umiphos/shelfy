from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from ..core.config import settings


@dataclass(frozen=True)
class Auth0Principal:
    subject: str
    claims: dict


bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Security(bearer_scheme),
]


@lru_cache
def _get_jwks_client() -> PyJWKClient:
    return PyJWKClient(
        f"{settings.auth0_issuer}.well-known/jwks.json",
        cache_keys=True,
    )


def _authentication_error(detail: str = "Token de acceso inválido") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_auth0_principal(
    credentials: BearerCredentials,
) -> Auth0Principal:
    if not settings.auth0_domain or not settings.auth0_audience:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth0 no está configurado en el servidor",
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _authentication_error("Se requiere un token de acceso")

    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=settings.auth0_algorithms,
            audience=settings.auth0_audience,
            issuer=settings.auth0_issuer,
        )
    except PyJWTError as exc:
        raise _authentication_error() from exc

    subject = claims.get("sub")
    if not subject:
        raise _authentication_error("El token no contiene una identidad válida")
    return Auth0Principal(subject=subject, claims=claims)


def require_permission(permission: str):
    def dependency(
        principal: Annotated[Auth0Principal, Security(get_auth0_principal)],
    ) -> Auth0Principal:
        permissions = principal.claims.get("permissions", [])
        if permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción",
            )
        return principal

    return dependency
