from functools import lru_cache
from pathlib import Path
import os
import json

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


class Settings:
    def __init__(self) -> None:
        self.api_host = os.getenv("API_HOST", "127.0.0.1")
        self.api_port = int(os.getenv("API_PORT", "8000"))
        self.api_env = os.getenv("API_ENV", "development")

        raw_cors_origins = os.getenv("CORS_ORIGINS", "*")
        self.cors_origins = [
            origin.strip() for origin in raw_cors_origins.split(",") if origin.strip()
        ] or ["*"]

        self.firebase_web_api_key = os.getenv("FIREBASE_WEB_API_KEY", "")
        if not self.firebase_web_api_key:
            raise ValueError("FIREBASE_WEB_API_KEY no está configurada.")

        # Nuevo: credenciales como JSON en variable de entorno
        firebase_credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON", "")
        if firebase_credentials_json:
            self.firebase_credentials = json.loads(firebase_credentials_json)
        else:
            # Fallback para desarrollo local con archivo
            path = Path(os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "serviceAccountKey.json"))
            if not path.is_absolute():
                path = (BASE_DIR / path).resolve()
            if not path.exists():
                raise FileNotFoundError(f"No se encontró el archivo de credenciales: {path}")
            with open(path) as f:
                self.firebase_credentials = json.load(f)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()