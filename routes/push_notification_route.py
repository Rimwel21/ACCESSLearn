from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from models.accounts import Accounts
from schemas.push_notification_schema import PushConfigOut, PushSubscriptionIn, PushSubscriptionOut
from services.push_notification_service import (
    delete_push_subscription,
    push_config,
    save_push_subscription,
    send_due_soon_deadline_notifications,
)
from utils.admin_guard import require_admin
from utils.dependencies import get_current_user, get_db


router = APIRouter(prefix="/notifications/push", tags=["Push Notifications"])


@router.get("/config", response_model=PushConfigOut)
def get_push_config():
    return push_config()


@router.post("/subscribe", response_model=PushSubscriptionOut)
def subscribe_to_push(
    subscription: PushSubscriptionIn,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return save_push_subscription(
        db,
        current_user,
        subscription,
        user_agent=request.headers.get("user-agent"),
    )


@router.delete("/unsubscribe")
def unsubscribe_from_push(
    endpoint: str | None = None,
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(get_current_user),
):
    return delete_push_subscription(db, current_user, endpoint)


@router.post("/deadline-reminders/run")
def run_deadline_reminders(
    db: Session = Depends(get_db),
    current_user: Accounts = Depends(require_admin),
):
    return {"sent": send_due_soon_deadline_notifications(db)}
