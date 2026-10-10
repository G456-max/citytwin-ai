"""
MineGuard AI - SQLAlchemy Database Models
Persistent entities for projects, cryptographic scan findings, and CBOM metadata.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    path = Column(String(1024), nullable=False, unique=True, index=True)
    scan_type = Column(String(50), default="source")
    created_at = Column(DateTime, default=utc_now)

    findings = relationship("FindingRecord", back_populates="project", cascade="all, delete-orphan")


class FindingRecord(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    file = Column(String(1024), nullable=False)
    line = Column(Integer, nullable=False, default=1)
    algorithm = Column(String(100), nullable=False, index=True)
    severity = Column(String(50), nullable=False, index=True)
    context = Column(Text, nullable=True)
    key_size = Column(Integer, nullable=True)
    pqc_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    project = relationship("Project", back_populates="findings")

    def to_dict(self):
        pqc_data = None
        if self.pqc_json:
            try:
                pqc_data = json.loads(self.pqc_json)
            except Exception:
                pqc_data = None

        return {
            "id": self.id,
            "project_id": self.project_id,
            "file": self.file,
            "line": self.line,
            "algorithm": self.algorithm,
            "severity": self.severity,
            "context": self.context,
            "key_size": self.key_size,
            "pqc": pqc_data,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
