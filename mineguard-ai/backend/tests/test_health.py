from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify GET /api/health returns 200 with service information and timestamp."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "MineGuard AI"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data


def test_root():
    """Verify GET / returns 200 with service links and documentation pointer."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "MineGuard AI"
    assert data["docs"] == "/docs"
    assert data["health"] == "/api/health"
    assert "tagline" in data


def test_scan_stub():
    """Verify POST /api/scan stub endpoint returns 200 with mock findings."""
    payload = {"project_path": "/test/mining-project", "scan_type": "source"}
    response = client.post("/api/scan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 8
    assert len(data["findings"]) == 8
    assert data["source"] == "simulation"


def test_risk_stub():
    """Verify POST /api/risk stub endpoint returns 200."""
    payload = {"findings": []}
    response = client.post("/api/risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "score" in data
    assert "severity" in data


def test_graph_stub():
    """Verify GET /api/graph stub endpoint returns 200."""
    response = client.get("/api/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data


def test_cascade_stub():
    """Verify POST /api/cascade stub endpoint returns 200."""
    payload = {"q_day": 2029, "migrated_nodes": []}
    response = client.post("/api/cascade", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["q_day"] == 2029
    assert "failed_nodes" in data


def test_priority_stub():
    """Verify POST /api/priority stub endpoint returns 200."""
    response = client.post("/api/priority")
    assert response.status_code == 200
    data = response.json()
    assert "priorities" in data


def test_plan_stub():
    """Verify POST /api/plan stub endpoint returns 200."""
    payload = {"budget_usd": 500000, "max_downtime_hours": 24, "deadline_weeks": 52}
    response = client.post("/api/plan", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "phases" in data
    assert "feasible" in data


def test_explain_stub():
    """Verify POST /api/explain stub endpoint returns 200."""
    payload = {"question": "What is Shor's algorithm?"}
    response = client.post("/api/explain", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


def test_scan_projects_and_findings():
    """Verify GET /api/scan/projects and GET /api/scan/projects/{id}/findings."""
    # Ensure at least one scan has completed
    client.post("/api/scan", json={"project_path": "/test/demo-mine", "scan_type": "source"})
    
    res = client.get("/api/scan/projects")
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) >= 1
    project_id = projects[0]["id"]

    res_findings = client.get(f"/api/scan/projects/{project_id}/findings")
    assert res_findings.status_code == 200
    findings = res_findings.json()
    assert len(findings) >= 1
    assert "algorithm" in findings[0]
    assert "pqc" in findings[0]


def test_cbom_enrich_and_export():
    """Verify POST /api/cbom/enrich-findings and GET /api/cbom/export/{project_id}."""
    enrich_payload = {"findings": [{"algorithm": "RSA-2048", "file": "main.py", "line": 5}]}
    r_enrich = client.post("/api/cbom/enrich-findings", json=enrich_payload)
    assert r_enrich.status_code == 200
    assert r_enrich.json()["findings"][0]["pqc"]["kem"] == "ML-KEM-768"

    # Export CBOM
    res = client.get("/api/scan/projects")
    project_id = res.json()[0]["id"]
    r_export = client.get(f"/api/cbom/export/{project_id}")
    assert r_export.status_code == 200
    assert r_export.json()["bomFormat"] == "CycloneDX"
    assert "attachment" in r_export.headers.get("content-disposition", "")

