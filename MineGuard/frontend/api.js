/**
 * MineGuard — Minimal 4-Feature API Client
 * Connects to FastAPI backend (http://localhost:8000) with robust instant offline fallback.
 */

const API_BASE_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  ? 'http://localhost:8000'
  : 'http://localhost:8000';

// In-browser mock data for guaranteed offline resilience
const FALLBACK_DATA = {
  findings: [
    { file: "infrastructure/pki/ca_root.py", line: 14, algorithm: "RSA-4096", severity: "HIGH" },
    { file: "services/auth/jwt_validator.js", line: 42, algorithm: "RSA-2048", severity: "HIGH" },
    { file: "gateway/ot_modbus_proxy.py", line: 88, algorithm: "RSA-2048", severity: "HIGH" },
    { file: "scada/ventilation_telemetry.py", line: 31, algorithm: "RSA-2048", severity: "HIGH" },
    { file: "dispatch/haulage_fleet.js", line: 67, algorithm: "ECDSA", severity: "HIGH" },
    { file: "sensors/seismic_logger.py", line: 53, algorithm: "ECDSA", severity: "HIGH" },
    { file: "config/legacy_tokens.yaml", line: 9, algorithm: "MD5", severity: "MEDIUM" },
    { file: "database/session_cache.py", line: 23, algorithm: "MD5", severity: "MEDIUM" }
  ],
  nodes: [
    { id: "ca-root", name: "CA-Root", algorithm: "RSA-4096", critical: true },
    { id: "auth-svc", name: "Auth-Svc", algorithm: "RSA-2048", critical: true },
    { id: "ot-gateway", name: "OT-Gateway", algorithm: "RSA-2048", critical: true },
    { id: "ventilation", name: "Ventilation", algorithm: "RSA-2048", critical: true },
    { id: "haulage", name: "Haulage", algorithm: "ECDSA", critical: true },
    { id: "geo-db", name: "Geo-DB", algorithm: "AES-256", critical: false }
  ],
  edges: [
    ["auth-svc", "ca-root"],
    ["ot-gateway", "auth-svc"],
    ["ventilation", "ot-gateway"],
    ["haulage", "ot-gateway"],
    ["geo-db", "ventilation"]
  ]
};

async function apiScan(projectPath) {
  try {
    const res = await fetch(`${API_BASE_URL}/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: projectPath })
    });
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('mineguard_scan', JSON.stringify(data));
      return data;
    }
  } catch (err) {
    console.warn('Backend unavailable, using instant client fallback:', err);
  }

  // Client fallback
  const high = 6;
  const medium = 2;
  const score = Math.min(100, high * 15 + medium * 5); // 95
  const fallback = {
    project_path: projectPath || "/path/to/mining-project",
    findings: FALLBACK_DATA.findings,
    risk: {
      score: 95,
      severity: "CRITICAL",
      high_count: 6,
      medium_count: 2,
      total_findings: 8
    }
  };
  localStorage.setItem('mineguard_scan', JSON.stringify(fallback));
  return fallback;
}

async function apiCascade(qDay, migrated = []) {
  try {
    const res = await fetch(`${API_BASE_URL}/cascade`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q_day: parseInt(qDay, 10), migrated })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend cascade unavailable, using client logic:', err);
  }

  // Client BFS cascade simulation
  const failing = qDay < 2029 ? ["RSA-2048"] : (qDay < 2031 ? ["RSA-2048", "ECDSA"] : ["RSA-2048", "ECDSA", "RSA-4096"]);
  const migSet = new Set(migrated.map(m => m.toLowerCase().replace(" ", "-")));

  const seed = FALLBACK_DATA.nodes
    .filter(n => failing.some(a => n.algorithm.includes(a)) && !migSet.has(n.id))
    .map(n => n.id);

  const failed = new Set(seed);
  const queue = [...seed];
  const timeline = seed.map(n => ({ hour: 0, node: n, status: "FAILED" }));
  let hour = 0;

  while (queue.length > 0) {
    hour += 2;
    const size = queue.length;
    for (let i = 0; i < size; i++) {
      const current = queue.shift();
      for (const [src, dst] of FALLBACK_DATA.edges) {
        if (dst === current && !failed.has(src) && !migSet.has(src)) {
          failed.add(src);
          queue.push(src);
          timeline.push({ hour, node: src, status: "FAILED" });
        }
      }
    }
  }

  return {
    q_day: parseInt(qDay, 10),
    failed: Array.from(failed),
    timeline,
    total_down: failed.size,
    total_systems: FALLBACK_DATA.nodes.length,
    hours_to_shutdown: timeline.length ? Math.max(...timeline.map(t => t.hour)) : 0
  };
}

async function apiPriority(cascadeResult = {}) {
  try {
    const res = await fetch(`${API_BASE_URL}/priority`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cascade: cascadeResult })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend priority unavailable, using client fallback:', err);
  }

  return {
    priorities: [
      { rank: 1, system: "CA-Root", action: "MIGRATE FIRST", reason: "Cascade trigger — stops root trust breach and all 12 dependent failures", algorithm: "RSA-4096", replacement: "ML-DSA-87" },
      { rank: 2, system: "OT-Gateway", action: "HIGH", reason: "Safety critical — controls ventilation telemetry and haulage interlocks", algorithm: "RSA-2048", replacement: "ML-KEM-768" },
      { rank: 3, system: "Auth-Svc", action: "HIGH", reason: "Access control hub — authenticates operator tokens across mine site", algorithm: "RSA-2048", replacement: "ML-DSA-65" },
      { rank: 4, system: "Ventilation", action: "MEDIUM", reason: "Safety system — underground air flow and gas dilution telemetry", algorithm: "RSA-2048", replacement: "ML-KEM-768" },
      { rank: 5, system: "Haulage", action: "MEDIUM", reason: "Production — automated truck guidance and collision prevention", algorithm: "ECDSA", replacement: "ML-DSA-65" }
    ]
  };
}

async function apiPlan(priorities = []) {
  try {
    const res = await fetch(`${API_BASE_URL}/plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ priorities })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend plan unavailable, using client fallback:', err);
  }

  const phases = [
    {
      phase: 1,
      label: "IMMEDIATE",
      timeframe: "Weeks 1–4",
      systems: ["CA-Root"],
      effort_weeks: 4,
      cost_usd: 60000,
      deliverable: "Re-sign internal root certificates & trust store anchors"
    },
    {
      phase: 2,
      label: "HIGH",
      timeframe: "Weeks 5–9",
      systems: ["OT-Gateway", "Auth-Svc"],
      effort_weeks: 5,
      cost_usd: 75000,
      deliverable: "Deploy hybrid TLS VPN & operator token validation"
    },
    {
      phase: 3,
      label: "MEDIUM",
      timeframe: "Weeks 10–14",
      systems: ["Ventilation", "Haulage"],
      effort_weeks: 5,
      cost_usd: 75000,
      deliverable: "Upgrade SCADA telemetry endpoints & automated haulage transceivers"
    }
  ];

  return {
    phases,
    total_systems: 5,
    total_cost_usd: 210000,
    total_weeks: 14,
    feasible: true
  };
}
