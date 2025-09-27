# tests/test_bff.py
import asyncio
import json
from uuid import uuid4
import pytest
import respx
from httpx import AsyncClient

from app.main import app, settings
from app.clients import MicroservicesClient

@pytest.mark.asyncio
@respx.mock
async def test_get_perfil_completo(monkeypatch):
    # prepare IDs
    pet_id = str(uuid4())
    user_id = str(uuid4())
    app_id = str(uuid4())

    # mock MS1 /pets/{id}
    pet_resp = {
        "id": pet_id,
        "name": "Fido",
        "species": "dog",
        "breed": "mixed",
        "birth_date": "2020-01-01",
        "adoption_center_id": str(uuid4()),
        "image_url": None,
        "created_at": "2023-01-01T12:00:00Z",
        "adoption_status": {
            "id": str(uuid4()),
            "pet_id": pet_id,
            "state": "available",
            "last_updated": "2024-01-01T12:00:00Z"
        },
        "vaccines": []
    }
    respx.get(f"{settings.MS1_URL}/pets/{pet_id}").respond(200, json=pet_resp)

    # mock MS3 /history/pet/{id}
    history_resp = {
        "pet_id": pet_id,
        "history": [{"date": "2024-02-01T10:00:00Z", "event": "checkup"}],
        "images": [],
        "details": "healthy",
        "user_id": user_id,
        "meta": {"weight": 12.5}
    }
    respx.get(f"{settings.MS3_URL}/history/pet/{pet_id}").respond(200, json=history_resp)

    # mock MS2 candidate endpoints for applications by pet
    apps_resp = [
        {
            "id": app_id,
            "userId": user_id,
            "petId": pet_id,
            "requestDate": "2024-03-01T10:00:00Z",
            "status": "pending",
            "statusDate": "2024-03-02T10:00:00Z",
            "message": "I love dogs"
        }
    ]
    respx.get(f"{settings.MS2_URL}/applications").mock(return_value=respx.Response(200, json=apps_resp))
    respx.get(f"{settings.MS2_URL}/requests").mock(return_value=respx.Response(404))
    respx.get(f"{settings.MS2_URL}/prev-requests").mock(return_value=respx.Response(404))

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get(f"/mascotas/{pet_id}/perfil_completo")
        assert r.status_code == 200
        data = r.json()
        assert data["mascota"]["id"] == pet_id
        assert data["historia"]["pet_id"] == pet_id
        assert len(data["solicitudes"]) == 1

@pytest.mark.asyncio
@respx.mock
async def test_get_adoptadas_fallback(monkeypatch):
    # simulate MS1 failing and MS2 returning approved requests
    pet_id = str(uuid4())
    # MS1 /pets?state=adopted returns 500
    respx.get(f"{settings.MS1_URL}/pets").respond(500)
    # MS2 /requests?status=approved returns a list with petId
    reqs = [
        {"id": str(uuid4()), "userId": str(uuid4()), "petId": pet_id, "requestDate": "2024-01-01T00:00:00Z",
         "status": "approved", "statusDate": "2024-02-01T00:00:00Z", "message": "ok"}
    ]
    respx.get(f"{settings.MS2_URL}/requests").respond(200, json=reqs)
    # MS1 /pets/{pet_id} when fetched later returns pet data
    pet_resp = {
        "id": pet_id,
        "name": "Luna",
        "species": "cat",
        "breed": "siamese",
        "birth_date": "2021-05-01",
        "adoption_center_id": str(uuid4()),
        "image_url": None,
        "created_at": "2023-01-01T12:00:00Z",
        "adoption_status": None,
        "vaccines": []
    }
    respx.get(f"{settings.MS1_URL}/pets/{pet_id}").respond(200, json=pet_resp)

    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/adoptadas")
        assert r.status_code == 200
        body = r.json()
        assert body["count"] == 1
        assert body["results"][0]["id"] == pet_id
