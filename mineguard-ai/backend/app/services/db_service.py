"""
MineGuard AI - Database Service
CRUD operations and persistence helpers for Projects and Findings.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.db_models import Project, FindingRecord


def get_or_create_project(db: Session, project_path: str, scan_type: str = "source") -> Project:
    """
    Retrieves existing project by path or creates a new Project record.
    """
    clean_path = str(Path(project_path).resolve())
    project = db.query(Project).filter(Project.path == clean_path).first()
    if not project:
        name = Path(clean_path).name or "mining-project"
        project = Project(
            name=name,
            path=clean_path,
            scan_type=scan_type
        )
        db.add(project)
        db.commit()
        db.refresh(project)
    else:
        project.scan_type = scan_type
        db.commit()
        db.refresh(project)
    return project


def save_findings(db: Session, project_id: int, findings: List[Dict[str, Any]]) -> List[FindingRecord]:
    """
    Replaces existing findings for a project with newly scanned and enriched findings.
    """
    # Clear prior findings for project
    db.query(FindingRecord).filter(FindingRecord.project_id == project_id).delete()

    records: List[FindingRecord] = []
    for f in findings:
        pqc_val = f.get("pqc")
        pqc_str = json.dumps(pqc_val) if pqc_val else None

        rec = FindingRecord(
            project_id=project_id,
            file=str(f.get("file", "")),
            line=int(f.get("line", 1)),
            algorithm=str(f.get("algorithm", "UNKNOWN")),
            severity=str(f.get("severity", "MEDIUM")),
            context=f.get("context"),
            key_size=f.get("key_size"),
            pqc_json=pqc_str
        )
        db.add(rec)
        records.append(rec)

    db.commit()
    for r in records:
        db.refresh(r)
    return records


def get_projects(db: Session) -> List[Project]:
    """Retrieves all registered projects."""
    return db.query(Project).order_by(Project.created_at.desc()).all()


def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """Retrieves a single project by its primary key ID."""
    return db.query(Project).filter(Project.id == project_id).first()


def get_project_findings(db: Session, project_id: int) -> List[FindingRecord]:
    """Retrieves all findings for a given project."""
    return db.query(FindingRecord).filter(FindingRecord.project_id == project_id).all()
