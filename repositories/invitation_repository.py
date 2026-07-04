from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.teacher_invitation import TeacherInvitation
from utils.enum import InvitationStatusEnum

class InvitationRepository:
    @staticmethod
    def create(db: Session, invitation: TeacherInvitation) -> TeacherInvitation:
        db.add(invitation)
        db.commit()
        db.refresh(invitation)
        return invitation

    @staticmethod
    def get_by_id(db: Session, invitation_id: int) -> Optional[TeacherInvitation]:
        return db.query(TeacherInvitation).filter(TeacherInvitation.id == invitation_id).first()

    @staticmethod
    def get_pending_by_email(db: Session, email: str) -> Optional[TeacherInvitation]:
        return (
            db.query(TeacherInvitation)
            .filter(
                TeacherInvitation.email == email,
                TeacherInvitation.status == InvitationStatusEnum.pending,
            )
            .first()
        )

    @staticmethod
    def list_invitations(
        db: Session,
        status: Optional[InvitationStatusEnum] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[int, List[TeacherInvitation]]:
        q = db.query(TeacherInvitation)
        if status:
            q = q.filter(TeacherInvitation.status == status)
        if search:
            q = q.filter(
                TeacherInvitation.email.ilike(f"%{search}%") |
                TeacherInvitation.full_name.ilike(f"%{search}%")
            )
        total = q.count()
        items = (
            q.order_by(desc(TeacherInvitation.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return total, items

    @staticmethod
    def update(db: Session, invitation: TeacherInvitation) -> TeacherInvitation:
        db.commit()
        db.refresh(invitation)
        return invitation

    @staticmethod
    def count_pending(db: Session) -> int:
        return db.query(TeacherInvitation).filter(TeacherInvitation.status == InvitationStatusEnum.pending).count()
