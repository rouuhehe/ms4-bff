# mock_all.py  -- simple mock servers for MS1, MS2, MS3
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import threading
import time
from uuid import uuid4

# --- MS1 mock (pets) on port 8001 ---
app_ms1 = FastAPI()

@app_ms1.get("/pets/{pet_id}")
def get_pet(pet_id: str):
    return {
        "id": pet_id,
        "name": "Fido-mock",
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

@app_ms1.get("/pets")
def list_pets(state: str = None, from_date: str = None, to_date: str = None):
    # return one adopted pet when state=adopted for testing
    if state == "adopted":
        pid = str(uuid4())
        return [{
            "id": pid,
            "name": "Luna-mock",
            "species": "cat",
            "breed": "siamese",
            "birth_date": "2021-05-01",
            "adoption_center_id": str(uuid4()),
            "image_url": None,
            "created_at": "2023-01-01T12:00:00Z",
            "adoption_status": None,
            "vaccines": []
        }]
    return []

# --- MS2 mock (requests) on port 8002 ---
app_ms2 = FastAPI()

@app_ms2.get("/applications")
def get_applications(petId: str = None, status: str = None):
    # if petId given, return a mock application
    if petId:
        return [{
            "id": str(uuid4()),
            "userId": str(uuid4()),
            "petId": petId,
            "requestDate": "2024-03-01T10:00:00Z",
            "status": "pending",
            "statusDate": "2024-03-02T10:00:00Z",
            "message": "I love this pet (mock)"
        }]
    # if status=approved return a list with one
    if status == "approved":
        pid = str(uuid4())
        return [{
            "id": str(uuid4()),
            "userId": str(uuid4()),
            "petId": pid,
            "requestDate": "2024-01-01T00:00:00Z",
            "status": "approved",
            "statusDate": "2024-02-01T00:00:00Z",
            "message": "approved mock"
        }]
    return []

@app_ms2.get("/requests")
def get_requests(status: str = None):
    return get_applications(status=status)

# --- MS3 mock (history) on port 3003 ---
app_ms3 = FastAPI()

@app_ms3.get("/history/pet/{pet_id}")
def get_history(pet_id: str):
    return {
        "_id": str(uuid4()),
        "pet_id": pet_id,
        "history": [{"date": "2024-02-01T10:00:00Z", "event": "checkup"}],
        "images": [],
        "details": "healthy (mock)",
        "user_id": str(uuid4()),
        "meta": {"weight": 12.5}
    }

# Run each app in a thread so we can start all 3 from single script
def run_app(app, host, port):
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    threads = []
    threads.append(threading.Thread(target=run_app, args=(app_ms1, "0.0.0.0", 8001), daemon=True))
    threads.append(threading.Thread(target=run_app, args=(app_ms2, "0.0.0.0", 8002), daemon=True))
    threads.append(threading.Thread(target=run_app, args=(app_ms3, "0.0.0.0", 3003), daemon=True))

    for t in threads:
        t.start()
        time.sleep(0.2)

    print("Mocks running: MS1->8001, MS2->8002, MS3->3003. Ctrl+C to quit.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping mocks.")
