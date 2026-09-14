"""Jobs d'analyse et findings structurés (façade autour du pipeline /analyser/)."""

import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id", ondelete="SET NULL"), nullable=True)
    slug = Column(String(255), index=True)
    filename = Column(String(255))
    storage_key = Column(String(500))
    status = Column(String(50), nullable=False, default="queued", index=True)
    error_message = Column(Text)
    result_summary = Column(JSONB)
    started_at = Column(DateTime(timezone=True))
    finished_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    findings = relationship("AnalysisFinding", back_populates="job", cascade="all, delete-orphan")


class AnalysisFinding(Base):
    __tablename__ = "analysis_findings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("analysis_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    detail = Column(Text)
    severity = Column(String(50))
    score = Column(Integer)
    source_question = Column(String(255))
    evidence = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("AnalysisJob", back_populates="findings")
