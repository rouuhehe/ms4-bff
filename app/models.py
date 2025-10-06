from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum

class AdoptionState(str, Enum):
    available = "available"
    adopted = "adopted"
    pending = "pending"
    unknown = "unknown"

class VaccineResponse(BaseModel):
    id: UUID
    pet_id: UUID
    type: str
    date: date

class AdoptionStatusResponse(BaseModel):
    id: UUID
    pet_id: UUID
    state: AdoptionState
    last_updated: datetime

class PetResponse(BaseModel):
    id: UUID
    name: str
    species: str
    breed: str
    birth_date: date
    adoption_center_id: UUID
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None
    adoption_status: Optional[AdoptionStatusResponse] = None
    vaccines: List[VaccineResponse] = []

class HistoryEvent(BaseModel):
    date: datetime
    event: str

class HistoryResponse(BaseModel):
    id: Optional[str] = Field(default=None, alias="_id")
    pet_id: UUID
    history: List[HistoryEvent] = []
    images: List[str] = []
    details: Optional[str] = None
    user_id: Optional[str] = None
    meta: Optional[Dict] = None

    model_config = {
        "populate_by_name": True,   # permite modelar usando name o alias
        "str_to_lower": False
    }

class ApplicationViewStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class ApplicationView(BaseModel):
    id: UUID
    userId: UUID
    petId: UUID
    requestDate: datetime
    status: ApplicationViewStatus
    statusDate: datetime
    message: str


try:
    VaccineResponse.model_rebuild()
except Exception:
    pass

try:
    AdoptionStatusResponse.model_rebuild()
except Exception:
    pass

try:
    PetResponse.model_rebuild()
except Exception:
    pass

try:
    HistoryEvent.model_rebuild()
    HistoryResponse.model_rebuild()
except Exception:
    pass

try:
    ApplicationView.model_rebuild()
except Exception:
    pass

# fuerza reconstrucción de modelos Pydantic (resuelve referencias pendientes)
for name in ("VaccineResponse","AdoptionStatusResponse","PetResponse","HistoryEvent","HistoryResponse","ApplicationView"):
    if name in globals():
        try:
            globals()[name].model_rebuild()
        except Exception:
            pass
