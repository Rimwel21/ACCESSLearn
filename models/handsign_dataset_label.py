from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint

from database.connection import Base
from utils.utc_now import utc_now


class HandsignDatasetLabel(Base):
    __tablename__ = "handsign_dataset_labels"
    __table_args__ = (UniqueConstraint("week", "label", name="uq_handsign_dataset_label_week_label"),)

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    week = Column(String(10), nullable=False, index=True)
    label = Column(String(80), nullable=False, index=True)
    samples_required = Column(Integer, nullable=False, default=40)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
