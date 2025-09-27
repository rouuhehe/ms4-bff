# app/clients.py
import asyncio
from typing import Any, Dict, List, Optional
import httpx
from uuid import UUID

from .circuit_breaker import CircuitBreaker
from .models import PetResponse, HistoryResponse, ApplicationView
from .config import Settings

class MicroservicesClient:
    def __init__(self, settings: Settings):
        self.ms1 = str(settings.MS1_URL).rstrip("/")
        self.ms2 = str(settings.MS2_URL).rstrip("/")
        self.ms3 = str(settings.MS3_URL).rstrip("/")
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(settings.HTTP_TIMEOUT_SECONDS))
        self.retries = settings.RETRIES
        self.cb = CircuitBreaker(fail_max=settings.CIRCUIT_FAIL_MAX, reset_timeout=settings.CIRCUIT_RESET_TIMEOUT)

    async def close(self):
        await self._client.aclose()

    async def _get(self, url: str, params: Dict[str, Any] = None):
        async def do_call():
            r = await self._client.get(url, params=params)
            r.raise_for_status()
            return r.json()

        last_exc = None
        for attempt in range(max(1, self.retries)):
            try:
                return await self.cb.call(do_call)
            except Exception as e:
                last_exc = e
                # short backoff
                await asyncio.sleep(0.2 * (attempt + 1))
        raise last_exc

    # MS1: pets
    async def get_pet(self, pet_id: UUID) -> PetResponse:
        url = f"{self.ms1}/pets/{pet_id}"
        data = await self._get(url)
        return PetResponse.model_validate(data)

    async def list_pets(self, state: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[PetResponse]:
        url = f"{self.ms1}/pets"
        params = {}
        if state: params["state"] = state
        if from_date: params["from"] = from_date
        if to_date: params["to"] = to_date
        data = await self._get(url, params=params)
        # expects a list
        return [PetResponse.model_validate(item) for item in data]

    # MS3: history
    async def get_history(self, pet_id: UUID) -> Optional[HistoryResponse]:
        url = f"{self.ms3}/history/pet/{pet_id}"
        try:
            data = await self._get(url)
        except Exception:
            return None
        return HistoryResponse.model_validate(data)

    async def get_applications_by_pet(self, pet_id: UUID) -> List[ApplicationView]:
        candidates = [
            (f"{self.ms2}/applications", {"petId": str(pet_id)}),
            (f"{self.ms2}/requests", {"petId": str(pet_id)}),
            (f"{self.ms2}/prev-requests", {"petId": str(pet_id)}),
        ]
        for url, params in candidates:
            try:
                data = await self._get(url, params=params)
                if not data:
                    continue
                if isinstance(data, dict):
                    data = [data]
                return [ApplicationView.model_validate(item) for item in data]
            except Exception:
                continue
        return []

    async def get_adopted_pets(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> List[PetResponse]:
        try:
            pets = await self.list_pets(state="adopted", from_date=from_date, to_date=to_date)
            if pets:
                return pets
        except Exception:
            pass

        try:
            url = f"{self.ms2}/requests"
            params = {"status": "approved"}
            if from_date: params["from"] = from_date
            if to_date: params["to"] = to_date
            data = await self._get(url, params=params)
            if not data:
                return []
            pet_ids = {item.get("petId") or item.get("pet_id") for item in data if item.get("petId") or item.get("pet_id")}
            pets = []
            for pid in pet_ids:
                try:
                    pets.append(await self.get_pet(UUID(pid)))
                except Exception:
                    continue
            return pets
        except Exception:
            return []