# app/api/auth_models.py
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr


# ─── Request models ───────────────────────────────────────────────────────────

class RegisterPayload(BaseModel):
    # Paso 1 — cuenta
    email: EmailStr
    password: str
    acceptedTerms: bool

    # Paso 2 — perfil
    nombre: str
    apodo: str
    fechaNacimiento: str
    descripcion: Optional[str] = ""
    esPublico: bool = True
    fotoPerfil: Optional[str] = ""
    provider: Literal["password", "google"] = "password"


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


# ─── Response models ──────────────────────────────────────────────────────────

class AuthUserResponse(BaseModel):
    uid: str
    email: str
    nombre: str
    apodo: str
    idToken: str          # Firebase ID token para que la app autentique lecturas
    refreshToken: str     # Para renovar el token sin re-login