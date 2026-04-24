from fastapi import APIRouter

from .models import (
    AchievementModel,
    ApiCollectionResponse,
    CareLogModel,
    FeedItemResponse,
    FriendshipModel,
    NotificationModel,
    PestModel,
    PlantPhotoModel,
    SpeciesModel,
    UserModel,
    UserPlantDetailResponse,
    UserPlantModel,
    UserProfileResponse,
)
from .services import get_collection, get_document, get_subcollection

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, timezone

router = APIRouter()


# ─────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────

@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


# ─────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────

@router.get("/api/users/{user_id}", response_model=UserModel)
def read_user(user_id: str) -> dict:
    return get_document("users", user_id)


@router.get("/api/users/{user_id}/profile", response_model=UserProfileResponse)
def read_user_profile(user_id: str) -> dict:
    user = get_document("users", user_id)

    favorite_plant = None
    favorite_plant_species = None
    favorite_plant_id = user.get("plantaFavoritaId")

    if isinstance(favorite_plant_id, str) and favorite_plant_id:
        favorite_plant = get_document("user_plants", favorite_plant_id)
        species_id = favorite_plant.get("speciesId")
        if isinstance(species_id, str) and species_id:
            favorite_plant_species = get_document("species", species_id)

    return {
        "user": user,
        "favoritePlant": favorite_plant,
        "favoritePlantSpecies": favorite_plant_species,
    }


# ─────────────────────────────────────────────
# SPECIES
# ─────────────────────────────────────────────

@router.get("/api/species", response_model=list[SpeciesModel])
def read_all_species() -> list[dict]:
    return get_collection("species")


@router.get("/api/species/{species_id}", response_model=SpeciesModel)
def read_species(species_id: str) -> dict:
    return get_document("species", species_id)


# ─────────────────────────────────────────────
# USER PLANTS
# ─────────────────────────────────────────────

@router.get("/api/users/{user_id}/plants", response_model=list[UserPlantModel])
def read_user_plants(user_id: str) -> list[dict]:
    return get_collection("user_plants", filters=[("userId", "==", user_id)])


@router.get("/api/plants/{plant_id}", response_model=UserPlantDetailResponse)
def read_plant_detail(plant_id: str) -> dict:
    plant   = get_document("user_plants", plant_id)
    species = get_document("species", plant["speciesId"])
    pests   = get_subcollection("user_plants", plant_id, "pests")
    photos  = get_collection("plant_photos", filters=[("plantId", "==", plant_id)])
    logs    = get_collection(
        "care_logs",
        filters=[("plantId", "==", plant_id)],
        order_by="date",
    )
    return {
        "plant":    plant,
        "species":  species,
        "pests":    pests,
        "photos":   photos,
        "careLogs": logs,
    }


# ─────────────────────────────────────────────
# PESTS  (subcolección de user_plants)
# ─────────────────────────────────────────────

@router.get("/api/plants/{plant_id}/pests", response_model=list[PestModel])
def read_plant_pests(plant_id: str) -> list[dict]:
    return get_subcollection("user_plants", plant_id, "pests")


@router.get("/api/plants/{plant_id}/pests/{pest_id}", response_model=PestModel)
def read_pest(plant_id: str, pest_id: str) -> dict:
    return get_document(f"user_plants/{plant_id}/pests", pest_id)


# ─────────────────────────────────────────────
# CARE LOGS
# ─────────────────────────────────────────────

@router.get("/api/users/{user_id}/care-logs", response_model=list[CareLogModel])
def read_user_care_logs(user_id: str) -> list[dict]:
    return get_collection(
        "care_logs",
        filters=[("userId", "==", user_id)],
        order_by="date",
    )


@router.get("/api/plants/{plant_id}/care-logs", response_model=list[CareLogModel])
def read_plant_care_logs(plant_id: str) -> list[dict]:
    return get_collection(
        "care_logs",
        filters=[("plantId", "==", plant_id)],
        order_by="date",
    )


# ─────────────────────────────────────────────
# PLANT PHOTOS
# ─────────────────────────────────────────────

@router.get("/api/plants/{plant_id}/photos", response_model=list[PlantPhotoModel])
def read_plant_photos(plant_id: str) -> list[dict]:
    return get_collection(
        "plant_photos",
        filters=[("plantId", "==", plant_id)],
        order_by="date",
    )


# ─────────────────────────────────────────────
# FRIENDSHIPS
# ─────────────────────────────────────────────

@router.get("/api/users/{user_id}/friends", response_model=list[FriendshipModel])
def read_user_friends(user_id: str) -> list[dict]:
    # Busca en ambas direcciones: el usuario puede ser A o B
    as_a = get_collection(
        "friendships",
        filters=[("userAId", "==", user_id), ("status", "==", "accepted")],
    )
    as_b = get_collection(
        "friendships",
        filters=[("userBId", "==", user_id), ("status", "==", "accepted")],
    )
    return as_a + as_b


@router.get("/api/users/{user_id}/friend-requests", response_model=list[FriendshipModel])
def read_friend_requests(user_id: str) -> list[dict]:
    return get_collection(
        "friendships",
        filters=[("userBId", "==", user_id), ("status", "==", "pending")],
    )


# ─────────────────────────────────────────────
# FEED DE AMIGOS
# ─────────────────────────────────────────────

@router.get("/api/users/{user_id}/feed", response_model=list[FeedItemResponse])
def read_user_feed(user_id: str) -> list[dict]:
    # Obtener amistades aceptadas
    as_a = get_collection(
        "friendships",
        filters=[("userAId", "==", user_id), ("status", "==", "accepted")],
    )
    as_b = get_collection(
        "friendships",
        filters=[("userBId", "==", user_id), ("status", "==", "accepted")],
    )

    # IDs de amigos
    friend_ids = [f["userBId"] for f in as_a] + [f["userAId"] for f in as_b]

    feed: list[dict] = []
    for friend_id in friend_ids:
        plants = get_collection(
            "user_plants",
            filters=[("userId", "==", friend_id)],
        )
        friend_user = get_document("users", friend_id)
        for plant in plants:
            species = get_document("species", plant["speciesId"])
            feed.append({
                "plant":   plant,
                "species": species,
                "user":    friend_user,
            })

    return feed


# ─────────────────────────────────────────────
# ACHIEVEMENTS
# ─────────────────────────────────────────────

@router.get("/api/users/{user_id}/achievements", response_model=list[AchievementModel])
def read_user_achievements(user_id: str) -> list[dict]:
    return get_collection(
        "achievements",
        filters=[("userId", "==", user_id)],
        order_by="unlockedAt",
    )


# ─────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────

@router.get("/api/users/{user_id}/notifications", response_model=list[NotificationModel])
def read_user_notifications(user_id: str) -> list[dict]:
    return get_collection(
        "notifications",
        filters=[("userId", "==", user_id)],
        order_by="createdAt",
    )


@router.get("/api/users/{user_id}/notifications/unread", response_model=list[NotificationModel])
def read_unread_notifications(user_id: str) -> list[dict]:
    return get_collection(
        "notifications",
        filters=[("userId", "==", user_id), ("read", "==", False)],
        order_by="createdAt",
    )


# ─────────────────────────────────────────────
# GENERIC COLLECTION  (debug / admin)
# ─────────────────────────────────────────────

@router.get("/api/collections/{collection_name}", response_model=ApiCollectionResponse)
def read_collection(collection_name: str) -> dict:
    items = get_collection(collection_name)
    return {
        "collection": collection_name,
        "count":      len(items),
        "items":      items,
    }

# ─── PATCH /api/plants/{plant_id} ────────────────────────────────────────────

class UpdatePlantPayload(BaseModel):
    nickname: Optional[str] = None
    status: Optional[Literal["healthy", "needs-attention", "in-treatment", "critical"]] = None
    notes: Optional[str] = None
    purchasePrice: Optional[float] = None
    hasActivePests: Optional[bool] = None
    lastWatered: Optional[str] = None
    lastFertilized: Optional[str] = None
    lastNutrients: Optional[str] = None

@router.patch("/api/plants/{plant_id}")
def update_plant(plant_id: str, payload: UpdatePlantPayload) -> dict:
    """Actualiza los campos editables de una planta."""
    plant = get_document("user_plants", plant_id)

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    from .services import update_document
    update_document("user_plants", plant_id, updates)

    return {**plant, **updates}

# ─── PATCH /api/users/{user_id} ──────────────────────────────────────────────

class UpdateUserPayload(BaseModel):
    nombre:      Optional[str]  = None
    apodo:       Optional[str]  = None
    descripcion: Optional[str]  = None
    esPublico:   Optional[bool] = None

@router.patch("/api/users/{user_id}")
def update_user(user_id: str, payload: UpdateUserPayload) -> dict:
    user = get_document("users", user_id)

    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["updatedAt"] = datetime.now(timezone.utc).isoformat()

    from .services import update_document
    update_document("users", user_id, updates)

    return {**user, **updates}