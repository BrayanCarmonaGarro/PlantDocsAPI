from typing import Literal

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────
# BASE
# ─────────────────────────────────────────────

class FirestoreBaseModel(BaseModel):
    id: str
    createdAt: str
    updatedAt: str


# ─────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────

class UserModel(FirestoreBaseModel):
    nombre: str
    apodo: str
    email: str
    fotoPerfil: str
    descripcion: str
    esPublico: bool
    fechaNacimiento: str
    fechaIngreso: str
    plantaFavoritaId: str | None = None
    nivelInsignia: str
    rachaActual: int
    rachaMáxima: int
    cantidadPlantas: int
    cantidadAmigos: int
    xp: int
    nivel: int
    ultimaRacha: str
    provider: Literal["password", "google"]
    acceptedTerms: bool
    themePreference: Literal["system", "light", "dark"] = "system"


# ─────────────────────────────────────────────
# SPECIES
# ─────────────────────────────────────────────

class SpeciesModel(FirestoreBaseModel):
    commonName: str
    scientificName: str
    family: str
    category: str
    classification: Literal["indoor", "outdoor", "both"]
    origin: str
    climate: str
    toxic: bool
    invasive: bool
    lightRequired: Literal["direct", "indirect", "shade"]
    maxHeightCm: int
    growthRate: Literal["slow", "moderate", "fast"]
    bloomingSeason: str | None = None
    daysBetweenWatering: int
    daysBetweenFertilizing: int
    daysBetweenNutrients: int
    photos: list[str] = Field(default_factory=list)
    dataSource: Literal["ai", "manual"]


# ─────────────────────────────────────────────
# USER PLANTS
# ─────────────────────────────────────────────

class UserPlantModel(FirestoreBaseModel):
    userId: str
    speciesId: str
    nickname: str
    status: Literal["healthy", "needs-attention", "in-treatment", "critical"]
    photos: list[str] = Field(default_factory=list)
    purchasePrice: float | None = None
    hasActivePests: bool = False
    acquisitionDate: str
    lastWatered: str | None = None
    lastFertilized: str | None = None
    lastNutrients: str | None = None
    notes: str | None = None


# ─────────────────────────────────────────────
# PESTS  (subcolección: user_plants/{plantId}/pests/{pestId})
# ─────────────────────────────────────────────

class PestModel(FirestoreBaseModel):
    name: str
    scientificName: str | None = None
    description: str
    status: Literal["active", "treated", "eradicated"]
    treatment: str | None = None
    photos: list[str] = Field(default_factory=list)
    detectedAt: str
    resolvedAt: str | None = None


# ─────────────────────────────────────────────
# CARE LOGS
# ─────────────────────────────────────────────

class CareLogModel(FirestoreBaseModel):
    plantId: str
    userId: str
    type: Literal[
        "watering",
        "fertilizing",
        "nutrients",
        "pest_inspection",
        "pest_treatment"
    ]
    pestId: str | None = None
    notes: str | None = None
    date: str


# ─────────────────────────────────────────────
# PLANT PHOTOS
# ─────────────────────────────────────────────

class PlantPhotoModel(FirestoreBaseModel):
    plantId: str
    userId: str
    url: str
    description: str | None = None
    date: str


# ─────────────────────────────────────────────
# FRIENDSHIPS
# ─────────────────────────────────────────────

class FriendshipModel(FirestoreBaseModel):
    userAId: str
    userBId: str
    status: Literal["pending", "accepted", "blocked"]


# ─────────────────────────────────────────────
# ACHIEVEMENTS
# ─────────────────────────────────────────────

class AchievementModel(FirestoreBaseModel):
    userId: str
    type: str
    name: str
    unlockedAt: str


# ─────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────

class NotificationModel(FirestoreBaseModel):
    userId: str
    type: Literal[
        "watering",
        "fertilizing",
        "nutrients",
        "pest_detected",
        "friend_request",
        "friend_accepted",
        "achievement_unlocked"
    ]
    plantId: str | None = None
    pestId: str | None = None
    senderId: str | None = None
    message: str
    read: bool = False


# ─────────────────────────────────────────────
# RESPONSE MODELS
# ─────────────────────────────────────────────

class UserProfileResponse(BaseModel):
    user: UserModel
    favoritePlant: UserPlantModel | None = None
    favoritePlantSpecies: SpeciesModel | None = None


class UserPlantDetailResponse(BaseModel):
    plant: UserPlantModel
    species: SpeciesModel
    pests: list[PestModel] = Field(default_factory=list)
    photos: list[PlantPhotoModel] = Field(default_factory=list)
    careLogs: list[CareLogModel] = Field(default_factory=list)


class FeedItemResponse(BaseModel):
    plant: UserPlantModel
    species: SpeciesModel
    user: UserModel


class ApiCollectionResponse(BaseModel):
    collection: str
    count: int
    items: list[dict]