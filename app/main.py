# app/main.py
import asyncio
from fastapi import FastAPI, HTTPException
from uuid import UUID
from .config import Settings
import redis.asyncio as aioredis

from .clients import MicroservicesClient
from .models import PetResponse, HistoryResponse
from .models import ApplicationView

app = FastAPI(title="MS4 - BFF (Mascotas)")

settings = Settings()

redis: aioredis.Redis | None = None
client: MicroservicesClient | None = None

def cache_key_perfil(mascota_id: str) -> str:
    return f"perfil:mascota:{mascota_id}"

@app.on_event("startup")
async def startup():
    global redis, client
    redis = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    client = MicroservicesClient(settings)

@app.on_event("shutdown")
async def shutdown():
    global redis, client
    if redis:
        await redis.close()
    if client:
        await client.close()

@app.get("/mascotas/{mascota_id}/perfil_completo")
async def get_perfil_completo(mascota_id: UUID):
    key = cache_key_perfil(str(mascota_id))
    cached = await redis.get(key)
    if cached:
        # Fast path: return cached JSON
        # Pydantic v2 supports parse_raw via model_validate_json but here we return raw dict
        import json
        return json.loads(cached)

    # fetch in parallel
    try:
        pet_task = asyncio.create_task(client.get_pet(mascota_id))
        history_task = asyncio.create_task(client.get_history(mascota_id))
        apps_task = asyncio.create_task(client.get_applications_by_pet(mascota_id))

        pet: PetResponse = await pet_task
        history: HistoryResponse | None = await history_task
        apps: list[ApplicationView] = await apps_task
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error consultando microservicios: {e}")

    # prepare composed response
    response = {
        "mascota": pet.model_dump(),
        "historia": history.model_dump() if history else None,
        "solicitudes": [a.model_dump() for a in apps]
    }

    # cache json string
    import json
    await redis.set(key, json.dumps(response, default=str), ex=settings.CACHE_TTL)
    return response

@app.get("/adoptadas")
async def get_adoptadas(from_date: str | None = None, to_date: str | None = None):
    try:
        pets = await client.get_adopted_pets(from_date=from_date, to_date=to_date)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"count": len(pets), "results": [p.model_dump() for p in pets]}