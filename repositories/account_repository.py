from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from models.accounts import Accounts
from utils.enum import AccountStatusEnum, RoleEnum

class AccountRepository:
    @staticmethod
    def get_by_id(db: Session, account_id: int) -> Optional[Accounts]:
        return db.query(Accounts).filter(Accounts.id == account_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[Accounts]:
        return db.query(Accounts).filter(Accounts.email == email).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[Accounts]:
        return db.query(Accounts).filter(Accounts.username == username).first()

    @staticmethod
    def list_accounts(
        db: Session,
        role: Optional[RoleEnum] = None,
        account_status: Optional[AccountStatusEnum] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[int, List[Accounts]]:
        q = db.query(Accounts).filter(Accounts.role != RoleEnum.admin)

        if role:
            q = q.filter(Accounts.role == role)
        if account_status:
            q = q.filter(Accounts.account_status == account_status)
        if search:
            q = q.filter(
                or_(
                    Accounts.username.ilike(f"%{search}%"),
                    Accounts.email.ilike(f"%{search}%"),
                )
            )

        total = q.count()
        items = (
            q.order_by(desc(Accounts.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return total, items

    @staticmethod
    def update_status(db: Session, account: Accounts, new_status: AccountStatusEnum) -> Accounts:
        account.account_status = new_status
        db.commit()
        db.refresh(account)
        return account

    @staticmethod
    def hard_delete(db: Session, account: Accounts) -> None:
        db.delete(account)
        db.commit()

    @staticmethod
    def bulk_status_update(db: Session, account_ids: List[int], status: AccountStatusEnum) -> int:
        count = (
            db.query(Accounts)
            .filter(Accounts.id.in_(account_ids), Accounts.role != RoleEnum.admin)
            .update({"account_status": status}, synchronize_session=False)
        )
        db.commit()
        return count

    @staticmethod
    def bulk_hard_delete(db: Session, account_ids: List[int]) -> int:
        count = (
            db.query(Accounts)
            .filter(
                Accounts.id.in_(account_ids),
                Accounts.role != RoleEnum.admin,
                Accounts.account_status == AccountStatusEnum.archived,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return count

    @staticmethod
    def count_by_status(db: Session, role: Optional[RoleEnum] = None, status: Optional[AccountStatusEnum] = None) -> int:
        q = db.query(Accounts)
        if role:
            q = q.filter(Accounts.role == role)
        if status:
            q = q.filter(Accounts.account_status == status)
        return q.count()
