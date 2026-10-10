/**
 * MineGuard AI - Backend API Integration Client
 * Base URL defaults to http://127.0.0.1:8000/api
 */

const API_BASE_URL = window.MINEGUARD_API_URL || "http://127.0.0.1:8000/api";

const MineGuardAPI = {
  baseUrl: API_BASE_URL,

  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const defaultHeaders = {
      "Content-Type": "application/json",
      "Accept": "application/json"
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...(options.headers || {})
        }
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error?.message || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (err) {
      console.warn(`[MineGuard API] Request to ${endpoint} failed:`, err.message);
      throw err;
    }
  },

  /**
   * Health Check: GET /api/health
   */
  async checkHealth() {
    return this.request("/health");
  },

  /**
   * Scan Project: POST /api/scan
   */
  async scanProject(projectPath, scanType = "source") {
    return this.request("/scan", {
      method: "POST",
      body: JSON.stringify({ project_path: projectPath, scan_type: scanType })
    });
  },

  /**
   * Calculate Risk: POST /api/risk
   */
  async calculateRisk(findings = []) {
    return this.request("/risk", {
      method: "POST",
      body: JSON.stringify({ findings })
    });
  },

  /**
   * Get Dependency Graph: GET /api/graph
   */
  async getGraph() {
    return this.request("/graph");
  },

  /**
   * Run Cascade Simulation: POST /api/cascade
   */
  async runCascade(qDay = 2029, migratedNodes = []) {
    return this.request("/cascade", {
      method: "POST",
      body: JSON.stringify({ q_day: qDay, migrated_nodes: migratedNodes })
    });
  },

  /**
   * Get Migration Priorities: POST /api/priority
   */
  async getPriorities() {
    return this.request("/priority", {
      method: "POST"
    });
  },

  /**
   * Generate Migration Plan: POST /api/plan
   */
  async generatePlan(budgetUsd = 2400000, maxDowntimeHours = 48, deadlineWeeks = 104) {
    return this.request("/plan", {
      method: "POST",
      body: JSON.stringify({
        budget_usd: budgetUsd,
        max_downtime_hours: maxDowntimeHours,
        deadline_weeks: deadlineWeeks
      })
    });
  },

  /**
   * AI Explain Query: POST /api/explain
   */
  async explain(question, context = "") {
    return this.request("/explain", {
      method: "POST",
      body: JSON.stringify({ question, context })
    });
  }
};

if (typeof window !== "undefined") {
  window.MineGuardAPI = MineGuardAPI;
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = MineGuardAPI;
}
