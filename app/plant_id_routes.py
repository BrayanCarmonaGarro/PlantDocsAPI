# app/plant_id_routes.py
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from .config import get_settings
from .firebase import get_firestore_client

router = APIRouter(prefix="/api/identify", tags=["identify"])

PLANT_ID_URL = "https://plant.id/api/v3/identification"

DETAILS = (
    "common_names,url,description,taxonomy,edible_parts,"
    "propagation_methods,watering,best_watering,best_light_condition,"
    "best_soil_type,toxicity,common_uses"
)

NON_TOXIC_PHRASES = [
    "not toxic", "non-toxic", "nontoxic", "no tóxic",
    "not poisonous", "not harmful", "generally safe",
    "safe for", "no es tóxic", "no es venenosa",
    "is not toxic", "are not toxic", "is not poisonous",
]

TOXIC_PHRASES = [
    "is toxic", "are toxic", "can be toxic", "toxic to",
    "is poisonous", "are poisonous", "poisonous to",
    "is harmful", "harmful if", "contains saponins",
    "contains toxins", "es tóxic", "es venenosa",
]


class IdentifyRequest(BaseModel):
    image_base64: str


class SpeciesResult(BaseModel):
    species_id: str
    commonName: str
    scientificName: str
    family: str
    probability: float
    description: str | None
    toxic: bool
    lightRequired: str
    daysBetweenWatering: int
    watering_info: str | None
    edible_parts: list[str]
    propagation_methods: list[str]
    photo_url: str | None


@router.post("", response_model=SpeciesResult)
async def identify_plant(body: IdentifyRequest):
    settings = get_settings()
    db = get_firestore_client()

    # ── 1. Llamar a Plant.id ──────────────────────────────────────────────────
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{PLANT_ID_URL}?details={DETAILS}&language=es",
            headers={"Api-Key": settings.plant_id_api_key, "Content-Type": "application/json"},
            json={
                "images": [f"data:image/jpeg;base64,{body.image_base64}"],
            },
        )

    if response.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail=f"Plant.id error: {response.text}")

    data = response.json()

    if not data.get("result", {}).get("is_plant", {}).get("binary", False):
        raise HTTPException(status_code=422, detail="No se detectó una planta en la imagen.")

    suggestions = data["result"]["classification"]["suggestions"]
    if not suggestions:
        raise HTTPException(status_code=422, detail="No se pudo identificar la planta.")

    top = suggestions[0]
    details = top.get("details", {})
    probability = round(top.get("probability", 0), 4)

    # ── Nombres ───────────────────────────────────────────────────────────────
    scientific_name = top.get("name", "Unknown")
    common_names = details.get("common_names") or []
    common_name = common_names[0] if common_names else scientific_name

    # ── Taxonomía ─────────────────────────────────────────────────────────────
    taxonomy = details.get("taxonomy") or {}
    family = taxonomy.get("family", "Unknown")

    # ── Descripción ───────────────────────────────────────────────────────────
    description_obj = details.get("description") or {}
    description = description_obj.get("value") if isinstance(description_obj, dict) else None

    # ── Toxicidad ─────────────────────────────────────────────────────────────
    toxicity_text = (details.get("toxicity") or "").lower()
    if any(phrase in toxicity_text for phrase in NON_TOXIC_PHRASES):
        is_toxic = False
    elif any(phrase in toxicity_text for phrase in TOXIC_PHRASES):
        is_toxic = True
    else:
        is_toxic = False  # sin evidencia clara → no tóxica

    # ── Luz ───────────────────────────────────────────────────────────────────
    light_raw = (details.get("best_light_condition") or "").lower()
    if "direct" in light_raw and "indirect" not in light_raw:
        light = "direct"
    elif "shade" in light_raw or "low light" in light_raw:
        light = "shade"
    else:
        light = "indirect"

    # ── Riego ─────────────────────────────────────────────────────────────────
    watering = details.get("watering") or {}
    watering_max = watering.get("max", 2)
    days_watering = max(1, round(7 / watering_max)) if watering_max else 7

    # ── Foto ──────────────────────────────────────────────────────────────────
    photos_list = details.get("images") or []
    photo_url = photos_list[0].get("value") if photos_list else None

    # ── Partes comestibles y propagación ─────────────────────────────────────
    edible_parts = details.get("edible_parts") or []
    propagation_methods = details.get("propagation_methods") or []

    # ── Buscar o crear la species en Firestore ────────────────────────────────
    species_ref = db.collection("species")
    existing = species_ref.where("scientificName", "==", scientific_name).limit(1).get()
    now = datetime.now(timezone.utc).isoformat()

    if existing:
        species_id = existing[0].id
    else:
        species_id = f"species-{uuid.uuid4().hex[:8]}"
        species_ref.document(species_id).set({
            "id": species_id,
            "commonName": common_name,
            "scientificName": scientific_name,
            "family": family,
            "category": "unknown",
            "classification": "both",
            "origin": "",
            "climate": "",
            "toxic": is_toxic,
            "invasive": False,
            "lightRequired": light,
            "maxHeightCm": 100,
            "growthRate": "moderate",
            "bloomingSeason": None,
            "daysBetweenWatering": days_watering,
            "daysBetweenFertilizing": 30,
            "daysBetweenNutrients": 60,
            "photos": [photo_url] if photo_url else [],
            "dataSource": "ai",
            "createdAt": now,
            "updatedAt": now,
        })

    # ── Siempre devuelve datos frescos de Plant.id ────────────────────────────
    return SpeciesResult(
        species_id=species_id,
        commonName=common_name,
        scientificName=scientific_name,
        family=family,
        probability=probability,
        description=description,
        toxic=is_toxic,
        lightRequired=light,
        daysBetweenWatering=days_watering,
        watering_info=details.get("best_watering"),
        edible_parts=edible_parts,
        propagation_methods=propagation_methods,
        photo_url=photo_url,
    )