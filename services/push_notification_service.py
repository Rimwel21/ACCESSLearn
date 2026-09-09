from __future__ import annotations

from datetime import timedelta
import json

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.config import settings
from models.accounts import Accounts
from models.push_notification import DeadlineNotificationLog, PushSubscription
from models.student_profile import StudentProfile
from models.teacher_assessment import TeacherAssessment
from models.teacher_class import TeacherClass
from models.teacher_module import TeacherModule
from schemas.push_notification_schema import PushSubscriptionIn
from utils.enum import RoleEnum
from utils.utc_now import utc_now


REMINDER_DAYS = (2, 1)


def push_config() -> dict[str, str | bool | None]:
    public_key = settings.VAPID_PUBLIC_KEY
    private_key = settings.VAPID_PRIVATE_KEY
    return {
        "enabled": bool(public_key and private_key),
        "public_key": public_key,
    }


def save_push_subscription(
    db: Session,
    current_user: Accounts,
    subscription: PushSubscriptionIn,
    user_agent: str | None = None,
) -> PushSubscription:
    existing = (
        db.query(PushSubscription)
        .filter(PushSubscription.endpoint == subscription.endpoint)
        .first()
    )

    if existing:
        existing.account_id = current_user.id
        existing.p256dh = subscription.keys.p256dh
        existing.auth = subscription.keys.auth
        existing.user_agent = user_agent
        existing.updated_at = utc_now()
        db.commit()
        db.refresh(existing)
        return existing

    saved = PushSubscription(
        account_id=current_user.id,
        endpoint=subscription.endpoint,
        p256dh=subscription.keys.p256dh,
        auth=subscription.keys.auth,
        user_agent=user_agent,
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


def delete_push_subscription(db: Session, current_user: Accounts, endpoint: str | None = None) -> dict[str, str]:
    query = db.query(PushSubscription).filter(PushSubscription.account_id == current_user.id)
    if endpoint:
        query = query.filter(PushSubscription.endpoint == endpoint)

    for subscription in query.all():
        db.delete(subscription)
    db.commit()
    return {"detail": "Push subscription removed"}


def notify_module_created(db: Session, module: TeacherModule) -> None:
    if module.status != "Published" or module.class_id is None:
        return

    _send_class_notification(
        db,
        module.class_id,
        title="New learning material",
        body=f"{module.title} is now available.",
        url=f"/student/modules/{module.id}",
    )


def notify_module_updated(db: Session, module: TeacherModule) -> None:
    if module.status != "Published" or module.class_id is None:
        return

    _send_class_notification(
        db,
        module.class_id,
        title="Learning material updated",
        body=f"{module.title} was updated by your teacher.",
        url=f"/student/modules/{module.id}",
    )


def notify_assessment_created(db: Session, assessment: TeacherAssessment) -> None:
    if assessment.class_id is None:
        return

    is_quiz = assessment.assessment_type == "quiz"
    _send_class_notification(
        db,
        assessment.class_id,
        title="New quiz" if is_quiz else "New activity",
        body=f"{assessment.title} was posted by your teacher.",
        url="/student/quiz" if is_quiz else "/student/activities",
    )


def send_due_soon_deadline_notifications(db: Session) -> int:
    if not push_config()["enabled"]:
        return 0

    total = 0
    now = utc_now()
    for days in REMINDER_DAYS:
        window_start = now + timedelta(days=days)
        window_end = window_start + timedelta(days=1)
        assessments = (
            db.query(TeacherAssessment)
            .filter(
                TeacherAssessment.class_id.isnot(None),
                TeacherAssessment.due_at.isnot(None),
                TeacherAssessment.due_at >= window_start,
                TeacherAssessment.due_at < window_end,
                TeacherAssessment.assessment_type.in_(["quiz", "activity"]),
            )
            .all()
        )

        for assessment in assessments:
            student_ids = _student_account_ids_for_class(db, assessment.class_id)
            pending_ids = [
                student_id for student_id in student_ids
                if not _deadline_log_exists(db, student_id, assessment, days)
            ]
            if not pending_ids:
                continue

            item_label = "quiz" if assessment.assessment_type == "quiz" else "activity"
            url = "/student/quiz" if assessment.assessment_type == "quiz" else "/student/activities"
            sent_count = send_push_to_accounts(
                db,
                pending_ids,
                title=f"{item_label.title()} deadline reminder",
                body=f"{assessment.title} is due in {days} day{'s' if days > 1 else ''}.",
                url=url,
            )
            for student_id in pending_ids:
                db.add(DeadlineNotificationLog(
                    student_id=student_id,
                    item_type=assessment.assessment_type,
                    item_id=assessment.id,
                    reminder_days=days,
                ))
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
            total += sent_count

    return total


def send_push_to_accounts(
    db: Session,
    account_ids: list[int],
    title: str,
    body: str,
    url: str,
) -> int:
    private_key = settings.VAPID_PRIVATE_KEY
    subject = settings.VAPID_SUBJECT or "mailto:admin@signhear.local"
    if not private_key or not account_ids:
        return 0

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        print("WARNING: pywebpush is not installed. Push notifications were not sent.")
        return 0

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
        "icon": "/favicon.svg",
    })
    subscriptions = (
        db.query(PushSubscription)
        .filter(PushSubscription.account_id.in_(account_ids))
        .all()
    )

    sent = 0
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth,
                    },
                },
                data=payload,
                vapid_private_key=private_key,
                vapid_claims={"sub": subject},
            )
            sent += 1
        except WebPushException as exc:
            status_code = getattr(getattr(exc, "response", None), "status_code", None)
            if status_code in {404, 410}:
                db.delete(subscription)
                db.commit()
            else:
                print(f"WARNING: Push notification failed: {exc}")
        except Exception as exc:
            print(f"WARNING: Push notification failed: {exc}")

    return sent


def _send_class_notification(db: Session, class_id: int, title: str, body: str, url: str) -> None:
    try:
        student_ids = _student_account_ids_for_class(db, class_id)
        send_push_to_accounts(db, student_ids, title=title, body=body, url=url)
    except Exception as exc:
        print(f"WARNING: Notification dispatch skipped: {exc}")


def _student_account_ids_for_class(db: Session, class_id: int | None) -> list[int]:
    if class_id is None:
        return []

    teacher_class = db.query(TeacherClass).filter(TeacherClass.id == class_id).first()
    if not teacher_class:
        return []

    rows = (
        db.query(StudentProfile.account_id)
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .filter(
            StudentProfile.section_id == teacher_class.section_id,
            Accounts.role == RoleEnum.student,
        )
        .all()
    )
    return [row.account_id for row in rows]


def _deadline_log_exists(db: Session, student_id: int, assessment: TeacherAssessment, reminder_days: int) -> bool:
    return (
        db.query(DeadlineNotificationLog.id)
        .filter(
            DeadlineNotificationLog.student_id == student_id,
            DeadlineNotificationLog.item_type == assessment.assessment_type,
            DeadlineNotificationLog.item_id == assessment.id,
            DeadlineNotificationLog.reminder_days == reminder_days,
        )
        .first()
        is not None
    )
