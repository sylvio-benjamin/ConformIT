"""Niveau A — catalogue ISO global (pas d'organization_id, pas de texte de norme)."""

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.database import Base


class IsoDeliverable(Base):
    __tablename__ = "iso_deliverables"

    iso_id = Column(Integer, primary_key=True)
    reference = Column(String(255), nullable=False, index=True)
    title_en = Column(Text)
    title_fr = Column(Text)
    deliverable_type = Column(String(20))
    supplement_type = Column(String(20))
    edition = Column(Integer)
    publication_date = Column(Date)
    ics_codes = Column(JSONB, default=list)
    owner_committee = Column(String(120), index=True)
    current_stage = Column(Integer, index=True)
    replaces = Column(JSONB, default=list)
    replaced_by = Column(JSONB, default=list)
    languages = Column(JSONB, default=list)
    pages_en = Column(Integer)
    scope_en = Column(Text)
    withdrawn = Column(Boolean, default=False, nullable=False, index=True)
    framework_code = Column(String(50), index=True)
    metadata_source = Column(String(80), default="iso_deliverables_metadata")
    official_source = Column(String(255), default="https://www.iso.org/open-data.html")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
