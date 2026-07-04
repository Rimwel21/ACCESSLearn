from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from models.section import Section
from models.accounts import Accounts
from utils.enum import SectionStatusEnum, GradeLevel

class SectionRepository:
    @staticmethod
    def create(db: Session, section: Section) -> Section:
        db.add(section)
        db.commit()
        db.refresh(section)
        return section

    @staticmethod
    def get_by_id(db: Session, section_id: int) -> Optional[Section]:
        return db.query(Section).filter(Section.id == section_id).first()

    @staticmethod
    def list_sections(
        db: Session,
        grade_level: Optional[GradeLevel] = None,
        status: Optional[SectionStatusEnum] = None,
        teacher_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> Tuple[int, List[Section]]:
        q = db.query(Section)
        if grade_level:
            q = q.filter(Section.grade_level == grade_level)
        if status:
            q = q.filter(Section.status == status)
        if teacher_id:
            q = q.filter(Section.teacher_id == teacher_id)

        total = q.count()
        items = (
            q.order_by(desc(Section.created_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return total, items

    @staticmethod
    def update(db: Session, section: Section) -> Section:
        db.commit()
        db.refresh(section)
        return section

    @staticmethod
    def get_student_count(db: Session, section_id: int) -> int:
        # Assuming there is a student profile or account link to section
        # For now, we might need a relationship in Section model to students
        # Since I haven't added student->section FK yet, I'll placeholder this.
        # Actually, let's assume we'll add student_profile.section_id later.
        return 0 # Placeholder

    @staticmethod
    def count_sections(db: Session, status: Optional[SectionStatusEnum] = None, without_teacher: bool = False) -> int:
        q = db.query(Section)
        if status:
            q = q.filter(Section.status == status)
        if without_teacher:
            q = q.filter(Section.teacher_id == None)
        return q.count()
