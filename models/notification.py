"""
Notification model.

Admin-facing notifications for system events, teacher actions,
student events, and security alerts.
"""
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from database.connection import Base
from utils.enum import NotificationPriorityEnum, NotificationCategoryEnum
from utils.utc_now import utc_now


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)

    recipient_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    recipient    = relationship("Accounts", foreign_keys=[recipient_id], back_populates="notifications_received")

    icon        = Column(String(10),  nullable=True)    # emoji or icon name
    title       = Column(String(255), nullable=False)
    description = Column(Text,        nullable=True)

    priority = Column(
        Enum(NotificationPriorityEnum),
        default=NotificationPriorityEnum.medium,
        nullable=False,
        index=True,
    )

    category = Column(
        Enum(NotificationCategoryEnum),
        default=NotificationCategoryEnum.system,
        nullable=False,
        index=True,
    )

    # Optional references for drill-down navigation
    related_user_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    related_page    = Column(String(255), nullable=True)  # e.g. "/admin/teachers/42"

    is_read    = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
