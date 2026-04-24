# app/api/keycloak.py
import httpx
import os
from functools import lru_cache
from jose import jwt, JWTError
from fastapi import HTTPException, status

# En keycloak.py
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://astonied-robert-cayenned.ngrok-free.dev/realms/plant_docs")
ALGORITHMS = ["RS256"]
CLIENT_ID = "plant_docs"


@lru_cache(maxsize=1)
def get_keycloak_public_keys() -> list[dict]:
    """Obtiene las claves públicas de Keycloak para verificar JWT."""
    response = httpx.get(f"{KEYCLOAK_URL}/protocol/openid-connect/certs")
    response.raise_for_status()
    return response.json()["keys"]


def verify_keycloak_token(token: str) -> dict:
    """Verifica y decodifica un JWT de Keycloak."""
    try:
        keys = get_keycloak_public_keys()
        payload = jwt.decode(
            token,
            keys,
            algorithms=ALGORITHMS,
            audience=CLIENT_ID,
            options={"verify_aud": False},  # Keycloak a veces no incluye audience
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token inválido: {str(e)}",
        )