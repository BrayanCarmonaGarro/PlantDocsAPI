from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .firebase import get_firestore_client
from .routes import router
from .auth_routes import router as auth_router


def create_app() -> FastAPI:
    settings = get_settings()

    # Inicializa Firebase Admin una sola vez al arrancar el servidor.
    # Todas las rutas que usen firebase_auth o firestore ya lo encontrarán listo.
    get_firestore_client()

    app = FastAPI(
        title="Plant Project API",
        version="1.0.0",
        description="API en FastAPI sobre Firebase Firestore para la app de plantas.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    app.include_router(auth_router)
    return app