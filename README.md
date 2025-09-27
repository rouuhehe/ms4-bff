# MS4 - BFF (Mascotas) - FastAPI

## Resumen
MS4 es un Backend-for-Frontend (BFF) que orquesta datos desde:
- **MS1** (Pets) — FastAPI / MySQL
- **MS2** (Requests / Applications) — Spring Boot / PostgreSQL
- **MS3** (Histories) — NestJS / MongoDB

Endpoints principales:
- `GET /mascotas/{id}/perfil_completo` → `{ mascota, historia, solicitudes }`
- `GET /adoptadas?from=YYYY-MM-DD&to=YYYY-MM-DD` → mascotas adoptadas

Incluye caché (Redis), retries simples, circuit breaker básico y tests (pytest + respx).

---

## Estructura recomendada

ms4-bff/
├─ app/
│ ├─ init.py
│ ├─ main.py
│ ├─ config.py
│ ├─ clients.py
│ ├─ circuit_breaker.py
│ └─ models.py
├─ tests/
│ └─ test_bff.py
├─ Dockerfile
├─ docker-compose.yml # Compose de desarrollo (MS4 + Redis)
├─ requirements.txt
└─ .env # NO subir a git


---

## .env (ejemplo) — NO subir al repo

MS1_URL=http://ms1:8000

MS2_URL=http://ms2:8080

MS3_URL=http://ms3:3003

REDIS_URL=redis://redis:6379/0
CACHE_TTL=30
HTTP_TIMEOUT_SECONDS=5
RETRIES=3
CIRCUIT_FAIL_MAX=5
CIRCUIT_RESET_TIMEOUT=20
DEBUG=false


---

## Desarrollo local (rápido)
Levanta Redis + MS4 (modo desarrollo) con el `docker-compose.yml` incluido en el repo:

```bash
docker-compose up --build
# o
docker-compose up --build -d