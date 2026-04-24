from typing import Any

from fastapi import HTTPException

from .firebase import get_firestore_client


def _serialize_value(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()

    if isinstance(value, list):
        return [_serialize_value(item) for item in value]

    if isinstance(value, dict):
        return {
            nested_key: _serialize_value(nested_value)
            for nested_key, nested_value in value.items()
        }

    return value


def _serialize_document(document) -> dict[str, Any]:
    payload = {
        key: _serialize_value(value) for key, value in document.to_dict().items()
    }
    payload["id"] = document.id
    return payload


def get_document(collection_name: str, document_id: str) -> dict[str, Any]:
    db = get_firestore_client()
    snapshot = db.collection(collection_name).document(document_id).get()

    if not snapshot.exists:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{document_id}' not found in '{collection_name}'.",
        )

    return _serialize_document(snapshot)


def get_collection(
    collection_name: str,
    *,
    filters: list[tuple[str, str, Any]] | None = None,
    order_by: str | None = None,
) -> list[dict[str, Any]]:
    db = get_firestore_client()
    query = db.collection(collection_name)

    for field_name, operator, value in filters or []:
        query = query.where(field_name, operator, value)

    if order_by:
        query = query.order_by(order_by)

    return [_serialize_document(document) for document in query.stream()]


def get_subcollection(
    parent_collection: str,
    parent_id: str,
    subcollection_name: str,
    *,
    filters: list[tuple[str, str, Any]] | None = None,
    order_by: str | None = None,
) -> list[dict[str, Any]]:
    """
    Lee una subcolección de Firestore.
    Ruta: {parent_collection}/{parent_id}/{subcollection_name}

    Ejemplo:
        get_subcollection("user_plants", "plant-1", "pests")
        → user_plants/plant-1/pests
    """
    db = get_firestore_client()
    query = (
        db.collection(parent_collection)
        .document(parent_id)
        .collection(subcollection_name)
    )

    for field_name, operator, value in filters or []:
        query = query.where(field_name, operator, value)

    if order_by:
        query = query.order_by(order_by)

    return [_serialize_document(document) for document in query.stream()]

def set_document(
    collection_name: str,
    document_id: str,
    data: dict[str, Any],
    *,
    merge: bool = False,
) -> None:
    """
    Escribe o fusiona un documento en Firestore.
    merge=True → equivale a setDoc con { merge: true }
    """
    db = get_firestore_client()
    db.collection(collection_name).document(document_id).set(data, merge=merge)


def update_document(
    collection_name: str,
    document_id: str,
    data: dict[str, Any],
) -> None:
    """Actualiza campos específicos de un documento (merge parcial)."""
    db = get_firestore_client()
    db.collection(collection_name).document(document_id).update(data)