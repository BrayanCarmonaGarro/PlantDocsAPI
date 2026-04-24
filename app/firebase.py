from functools import lru_cache

import firebase_admin
from firebase_admin import credentials, firestore

from .config import get_settings


@lru_cache(maxsize=1)
def get_firestore_client() -> firestore.Client:
    settings = get_settings()

    if not firebase_admin._apps:
        credential = credentials.Certificate(settings.firebase_credentials)
        firebase_admin.initialize_app(credential)

    return firestore.client()