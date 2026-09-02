import datetime
from typing import Dict, Any

class AuditReportGenerator:
    """Generates structured executive compliance audit reports from spatial overlay analytics."""

    @staticmethod
    def generate_json_summary(
        audit_results: Dict[str, Any], 
        project_name: str = "City Corridor Expansion"
    ) -> Dict[str, Any]:
        """
        Formats raw discrepancy data into a structured, executive summary audit log.

        Args:
            audit_results: Dictionary summary output by CorridorDiscrepancyAuditor.
            project_name: Name of the corridor project being audited.

        Returns:
            Structured audit report dictionary.
        """
        violations = audit_results.get("violations", [])
        total_violations = len(violations)
        
        # Calculate severity counts
        critical_count = sum(1 for v in violations if v["severity"] == "Critical")
        medium_count = sum(1 for v in violations if v["severity"] == "Medium")
        low_count = sum(1 for v in violations if v["severity"] == "Low")
        
        # Calculate Corridor Clearance Percentage
        # Deduct compliance score based on severity weights:
        # Critical = -20%, Medium = -10%, Low = -3%
        clearance_deductions = (critical_count * 20) + (medium_count * 10) + (low_count * 3)
        clearance_percentage = max(100 - clearance_deductions, 0)
        
        # High Risk flags represent Critical & Medium deviations
        high_risk_count = critical_count + medium_count
        
        # Compliance Status tagging
        if total_violations > 0:
            status = "NON-COMPLIANT - ACTION REQUIRED"
        else:
            status = "COMPLIANT"
            
        report = {
            "project_name": project_name,
            "audit_timestamp": datetime.datetime.now().isoformat(),
            "compliance_summary": {
                "status": status,
                "corridor_clearance_percentage": round(float(clearance_percentage), 2),
                "total_violations_count": total_violations,
                "high_risk_violations_count": high_risk_count,
                "total_encroached_area_m2": round(float(audit_results.get("total_encroachment_area_m2", 0.0)), 2)
            },
            "violations_breakdown": {
                "critical_risk": critical_count,
                "medium_risk": medium_count,
                "low_risk": low_count
            },
            "detailed_audit_logs": violations
        }
        
        return report
