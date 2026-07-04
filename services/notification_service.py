"""
Notification Service.

Creates, lists, marks as read, and deletes notifications for admin accounts.
"""
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Session

from models.notification import Notification
from repositories.notification_repository import NotificationRepository
from utils.enum import NotificationPriorityEnum, NotificationCategoryEnum


def create_notification(
    db: Session,
    *,
    recipient_id:    int,
    title:           str,
    description:     Optional[str]                   = None,
    icon:            Optional[str]                   = None,
    priority:        NotificationPriorityEnum         = NotificationPriorityEnum.medium,
    category:        NotificationCategoryEnum         = NotificationCategoryEnum.system,
    related_user_id: Optional[int]                   = None,
    related_page:    Optional[str]                   = None,
) -> Notification:
    notif = Notification(
        recipient_id    = recipient_id,
        title           = title,
        description     = description,
        icon            = icon,
        priority        = priority,
        category        = category,
        related_user_id = related_user_id,
        related_page    = related_page,
    )
    return NotificationRepository.create(db, notif)


def get_notifications(
    db:           Session,
    recipient_id: int,
    *,
    unread_only:  bool                              = False,
    category:     Optional[NotificationCategoryEnum] = None,
    priority:     Optional[NotificationPriorityEnum] = None,
    page:         int                               = 1,
    per_page:     int                               = 30,
):
    return NotificationRepository.list_notifications(
        db,
        recipient_id=recipient_id,
        unread_only=unread_only,
        category=category,
        priority=priority,
        page=page,
        per_page=per_page
    )


def unread_count(db: Session, recipient_id: int) -> int:
    return NotificationRepository.unread_count(db, recipient_id)


def mark_read(db: Session, notification_id: int, recipient_id: int) -> Optional[Notification]:
    notif = NotificationRepository.get_by_id(db, notification_id, recipient_id)
    if notif:
        notif.is_read = True
        db.commit()
        db.refresh(notif)
    return notif


def mark_all_read(db: Session, recipient_id: int):
    return NotificationRepository.mark_all_read(db, recipient_id)


def delete_notification(db: Session, notification_id: int, recipient_id: int) -> bool:
    notif = NotificationRepository.get_by_id(db, notification_id, recipient_id)
    if notif:
        NotificationRepository.delete(db, notif)
        return True
    return False


def delete_all_notifications(db: Session, recipient_id: int):
    return NotificationRepository.delete_all(db, recipient_id)
