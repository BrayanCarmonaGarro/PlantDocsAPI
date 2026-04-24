# app/api/auth_routes.py
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .keycloak import verify_keycloak_token
from .services import get_document, set_document

router = APIRouter(tags=["auth"])
bearer = HTTPBearer()


# ─── Dependency: verifica token de Keycloak ───────────────────────────────────

def get_current_uid(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    payload = verify_keycloak_token(credentials.credentials)
    uid = payload.get("sub")
    if not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin subject"
        )
    return uid


# ─── GET /api/auth/me ─────────────────────────────────────────────────────────

@router.get("/api/auth/me")
def me(uid: str = Depends(get_current_uid)) -> dict:
    """Devuelve el perfil del usuario autenticado a partir de su token de Keycloak."""
    try:
        user = get_document("users", uid)
        return user
    except HTTPException:
        # Usuario nuevo que aún no tiene perfil en Firestore
        return {"uid": uid, "message": "Usuario nuevo, perfil no creado aún"}


# ─── POST /api/auth/me ────────────────────────────────────────────────────────

@router.post("/api/auth/me")
def create_profile(
    uid: str = Depends(get_current_uid),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """Crea el perfil en Firestore si el usuario es nuevo."""
    from .keycloak import verify_keycloak_token
    token_data = verify_keycloak_token(credentials.credentials)

    try:
        # Si ya existe, lo devolvemos
        return get_document("users", uid)
    except HTTPException:
        pass

    # Crear perfil básico con datos del token de Keycloak
    now = datetime.now(timezone.utc).isoformat()
    profile = {
        "email":            token_data.get("email", ""),
        "nombre":           token_data.get("name", ""),
        "apodo":            token_data.get("preferred_username", ""),
        "fotoPerfil":       token_data.get("picture", ""),
        "descripcion":      "",
        "esPublico":        True,
        "fechaNacimiento":  "",
        "acceptedTerms":    True,
        "provider":         "google",
        "themePreference":  "system",
        "fechaIngreso":     now,
        "createdAt":        now,
        "updatedAt":        now,
        "nivel":            0,
        "nivelInsignia":    "",
        "xp":               0,
        "rachaActual":      0,
        "rachaMáxima":      0,
        "ultimaRacha":      "",
        "cantidadAmigos":   0,
        "cantidadPlantas":  0,
        "plantaFavoritaId": "",
    }

    set_document("users", uid, profile)
    return {**profile, "id": uid}