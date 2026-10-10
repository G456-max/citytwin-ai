# MineGuard AI — Backend Service

> **"Predict the risk. Trace the impact. Plan the migration."**

MineGuard AI is an intelligent post-quantum cybersecurity platform engineered specifically for safety-critical mining and operational technology (OT) infrastructure.

---

## Architecture Overview (Phase A1 Foundation)

The backend is built with **FastAPI** following clean architectural patterns:

- **`app/main.py`**: Application factory, CORS middleware, global exception handlers, lifecycle events, and route mounting.
- **`app/config.py`**: Type-safe configuration management powered by `pydantic-settings`.
- **`app/database.py`**: SQLite database session management and SQLAlchemy ORM initialization.
- **`app/models/`**:
  - `schemas.py`: Pydantic models for request/response serialization across all planned endpoints.
  - `db_models.py`: Database entities.
- **`app/routes/`**:
  - `health.py`: Health check and system uptime status (`/api/health`).
  - `scan.py`: Cryptographic asset discovery & static analysis (`/api/scan`).
  - `risk.py`: Quantum vulnerability scoring (`/api/risk`).
  - `graph.py`: Mining dependency topology graph (`/api/graph`).
  - `cascade.py`: Quantum failure cascade simulation (`/api/cascade`).
  - `priority.py`: Migration prioritization ranking (`/api/priority`).
  - `plan.py`: ILP-optimized migration scheduling (`/api/plan`).
  - `explain.py`: Post-quantum security advisory assistant (`/api/explain`).
  - `monitoring.py` & `cbom.py`: Placeholders for CBOM ingestion and telemetry monitoring.
- **`app/engines/`**, **`app/ml/`**, **`app/rag/`**, **`app/services/`**, **`app/utils/`**: Modular packages reserved for upcoming implementation phases (B1–F7).
- **`tests/`**: Pytest test suite covering health checks and stub validation.

---

## Getting Started

### 1. Prerequisites
- Python 3.11+
- Virtual environment (recommended)

### 2. Install Dependencies
```bash
cd mineguard-ai/backend
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 4. Run the Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API Base: `http://localhost:8000/api`
- Interactive API Docs (Swagger): `http://localhost:8000/docs`
- Alternative Docs (ReDoc): `http://localhost:8000/redoc`
- Health Endpoint: `http://localhost:8000/api/health`

---

## Running Tests

Run the complete test suite with verbose output:

```bash
pytest tests -v
```
