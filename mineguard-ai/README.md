# MineGuard AI

> **"Predict the risk. Trace the impact. Plan the migration."**

MineGuard AI is an intelligent Post-Quantum Cybersecurity platform engineered for safety-critical mining and industrial operational technology (OT) infrastructure.

---

## Project Structure

```
mineguard-ai/
├── backend/                  # FastAPI backend service
│   ├── app/
│   │   ├── main.py           # Application entrypoint & middleware
│   │   ├── config.py         # Pydantic settings & environment configuration
│   │   ├── database.py       # SQLite database engine & session provider
│   │   ├── models/           # Pydantic schemas & SQLAlchemy ORM models
│   │   ├── routes/           # REST API routes (health, scan, risk, graph, cascade, priority, plan, explain)
│   │   ├── services/         # Business services & persistence
│   │   ├── engines/          # Cryptographic scanner, PQC mapper & CBOM parser
│   │   ├── ml/               # Machine learning feature pipelines
│   │   ├── rag/              # PQC guidance knowledge base & retrieval
│   │   └── utils/            # Logging, exceptions, middleware, validators
│   ├── tests/                # Automated pytest test suite
│   ├── data/                 # Data directory
│   ├── logs/                 # Structured log files
│   ├── requirements.txt      # Python dependencies
│   └── README.md
├── frontend/                 # Interactive 6-page web interface
│   ├── page1.html            # Scan Configuration
│   ├── page2.html            # Cryptographic Inventory & Risk Analysis
│   ├── page3.html            # Mining Dependency Network Graph
│   ├── page4.html            # Quantum Risk Cascade Simulator
│   ├── page5.html            # PQC Migration Roadmap & Resource Planner
│   ├── page6.html            # Verification, CBOM & Report Export
│   ├── css/                  # Styling assets
│   │   └── api.css           # Backend API integration styling
│   └── js/                   # Frontend logic
│       └── api.js            # Frontend REST client for backend API
└── README.md
```

---

## Quick Start

### 1. Launch the Backend
```bash
cd mineguard-ai/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- Open Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### 2. Run Backend Tests
```bash
cd mineguard-ai/backend
pytest tests -v
```

### 3. Open the Frontend
Open `mineguard-ai/frontend/page1.html` in your browser, or serve it using your preferred static web server.
