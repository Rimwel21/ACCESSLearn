from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from database.connection import Base
from utils.enum import SectionStatusEnum
from utils.utc_now import utc_now

class SchoolYear(Base):
    __tablename__ = "school_years"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False) # e.g. "2026-2027"
    is_current = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(SectionStatusEnum), default=SectionStatusEnum.active, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
