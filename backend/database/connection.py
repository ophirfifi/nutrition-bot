import base64
import json
import logging

import firebase_admin
from firebase_admin import credentials, firestore_async

from config import settings

logger = logging.getLogger(__name__)

_db: firestore_async.AsyncClient | None = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK. Called once at app startup."""
    if firebase_admin._apps:
        return  # already initialized

    if settings.firebase_credentials_base64:
        creds_dict = json.loads(base64.b64decode(settings.firebase_credentials_base64))
        cred = credentials.Certificate(creds_dict)
    elif settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
    else:
        raise RuntimeError(
            "Firebase credentials not configured. "
            "Set FIREBASE_CREDENTIALS_BASE64 or FIREBASE_CREDENTIALS_PATH."
        )

    firebase_admin.initialize_app(cred, {"projectId": settings.firebase_project_id})
    logger.info("Firebase initialized (project: %s)", settings.firebase_project_id)


def get_db() -> firestore_async.AsyncClient:
    """Return the singleton async Firestore client."""
    global _db
    if _db is None:
        _db = firestore_async.client()
    return _db
