from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from database.connection import Base
from utils.utc_now import utc_now


class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False, unique=True)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    account = relationship("Accounts", back_populates="push_subscriptions")


class DeadlineNotificationLog(Base):
    __tablename__ = "deadline_notification_logs"
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "item_type",
            "item_id",
            "reminder_days",
            name="uq_deadline_notification_once",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(20), nullable=False)
    item_id = Column(Integer, nullable=False, index=True)
    reminder_days = Column(Integer, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
