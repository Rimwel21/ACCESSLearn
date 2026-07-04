"""
AuditLog model.

Immutable append-only record of every meaningful admin and system action.
Old/new values stored as JSON text so any field can be tracked without
schema changes. Browser, OS, and IP captured from request headers.
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Text
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import AuditActionEnum, RoleEnum
from utils.utc_now import utc_now


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Who performed the action
    user_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True, index=True)
    actor   = relationship("Accounts", foreign_keys=[user_id], back_populates="audit_logs")
    role    = Column(Enum(RoleEnum), nullable=True)

    # What happened
    module          = Column(String(50), nullable=False)   # e.g. "AccountManagement"
    action          = Column(Enum(AuditActionEnum), nullable=False, index=True)
    affected_record = Column(String(255), nullable=True)   # e.g. "Teacher #42"

    # Change tracking (JSON strings, nullable if not applicable)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)

    # Context — old/new section and teacher for transfer events
    old_section_id  = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    new_section_id  = Column(Integer, ForeignKey("sections.id", ondelete="SET NULL"), nullable=True)
    old_teacher_id  = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    new_teacher_id  = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    reason          = Column(Text, nullable=True)

    # Request metadata
    ip_address  = Column(String(50), nullable=True)
    user_agent  = Column(Text, nullable=True)
    browser     = Column(String(100), nullable=True)
    os_name     = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)
    location    = Column(String(150), nullable=True)

    status     = Column(String(20), default="success", nullable=False)  # success | failed
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
