from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.notification import Notification
from utils.enum import NotificationPriorityEnum, NotificationCategoryEnum

class NotificationRepository:
    @staticmethod
    def create(db: Session, notification: Notification) -> Notification:
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def get_by_id(db: Session, notification_id: int, recipient_id: int) -> Optional[Notification]:
        return (
            db.query(Notification)
            .filter(Notification.id == notification_id, Notification.recipient_id == recipient_id)
            .first()
        )

    @staticmethod
    def list_notifications(
        db: Session,
        recipient_id: int,
        unread_only: bool = False,
        category: Optional[NotificationCategoryEnum] = None,
        priority: Optional[NotificationPriorityEnum] = None,
        page: int = 1,
        per_page: int = 30,
    ) -> Tuple[int, List[Notification]]:
        q = db.query(Notification).filter(Notification.recipient_id == recipient_id)

        if unread_only:
            q = q.filter(Notification.is_read == False)
        if category:
            q = q.filter(Notification.category == category)
        if priority:
            q = q.filter(Notification.priority == priority)

        total = q.count()
        items = (
            q.order_by(desc(Notification.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return total, items

    @staticmethod
    def unread_count(db: Session, recipient_id: int) -> int:
        return (
            db.query(Notification)
            .filter(Notification.recipient_id == recipient_id, Notification.is_read == False)
            .count()
        )

    @staticmethod
    def mark_all_read(db: Session, recipient_id: int) -> int:
        count = (
            db.query(Notification)
            .filter(Notification.recipient_id == recipient_id, Notification.is_read == False)
            .update({"is_read": True}, synchronize_session=False)
        )
        db.commit()
        return count

    @staticmethod
    def delete(db: Session, notification: Notification) -> None:
        db.delete(notification)
        db.commit()

    @staticmethod
    def delete_all(db: Session, recipient_id: int) -> int:
        count = (
            db.query(Notification)
            .filter(Notification.recipient_id == recipient_id)
            .delete(synchronize_session=False)
        )
        db.commit()
        return count
