from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.audit_log import AuditLog
from utils.enum import AuditActionEnum, RoleEnum
from datetime import datetime

class AuditLogRepository:
    @staticmethod
    def create(db: Session, log: AuditLog) -> AuditLog:
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def list_logs(
        db: Session,
        module: Optional[str] = None,
        action: Optional[AuditActionEnum] = None,
        actor_role: Optional[RoleEnum] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 25,
    ) -> Tuple[int, List[AuditLog]]:
        q = db.query(AuditLog)

        if module:
            q = q.filter(AuditLog.module.ilike(f"%{module}%"))
        if action:
            q = q.filter(AuditLog.action == action)
        if actor_role:
            q = q.filter(AuditLog.role == actor_role)
        if date_from:
            q = q.filter(AuditLog.created_at >= date_from)
        if date_to:
            q = q.filter(AuditLog.created_at <= date_to)
        if search:
            q = q.filter(AuditLog.affected_record.ilike(f"%{search}%"))

        total = q.count()
        items = (
            q.order_by(desc(AuditLog.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return total, items
