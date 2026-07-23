from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from database.connection import engine
from models.HI_sections import HI_SECTIONS
from models.grade_levels import GradeLevels
from models.teacher_grade_handles import TeacherGradeHandles
from utils.enum import SectionStatusEnum


def ensure_academic_tables() -> None:
    """Create legacy academic tables when an existing DB is missing them."""
    inspector = inspect(engine)

    if not inspector.has_table(GradeLevels.__tablename__):
        GradeLevels.__table__.create(bind=engine, checkfirst=True)

    inspector = inspect(engine)
    if not inspector.has_table(HI_SECTIONS.__tablename__):
        HI_SECTIONS.__table__.create(bind=engine, checkfirst=True)

    _ensure_teacher_grade_handles_schema()
    _seed_default_academic_options()


def _seed_default_academic_options() -> None:
    with Session(engine) as db:
        grade_levels = db.query(GradeLevels).order_by(GradeLevels.id.asc()).all()

        if not grade_levels:
            grade_levels = [
                GradeLevels(name=f"Grade {level}", status=SectionStatusEnum.active)
                for level in range(1, 7)
            ]
            db.add_all(grade_levels)
            db.commit()

        section_count = db.query(HI_SECTIONS).count()
        if section_count:
            return

        grade_levels = db.query(GradeLevels).order_by(GradeLevels.id.asc()).all()
        db.add_all([
            HI_SECTIONS(name="Section A", grade_level_id=grade_level.id)
            for grade_level in grade_levels
        ])
        db.commit()


def _ensure_teacher_grade_handles_schema() -> None:
    inspector = inspect(engine)
    table_name = TeacherGradeHandles.__tablename__

    if not inspector.has_table(table_name):
        TeacherGradeHandles.__table__.create(bind=engine, checkfirst=True)
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}

    with engine.begin() as connection:
        if "grade_level_id" not in columns:
            connection.execute(text(
                "ALTER TABLE teacher_grade_handles "
                "ADD COLUMN IF NOT EXISTS grade_level_id INTEGER REFERENCES grade_levels(id)"
            ))

        if "grade_level_handles" in columns:
            connection.execute(text(
                "ALTER TABLE teacher_grade_handles "
                "ALTER COLUMN grade_level_handles DROP NOT NULL"
            ))

            connection.execute(text(
                """
                UPDATE teacher_grade_handles AS handles
                SET grade_level_id = grade_levels.id
                FROM grade_levels
                WHERE handles.grade_level_id IS NULL
                  AND handles.grade_level_handles IS NOT NULL
                  AND lower(replace(grade_levels.name, ' ', '_')) = lower(handles.grade_level_handles::text)
                """
            ))

        connection.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_teacher_grade_handles_grade_level_id "
            "ON teacher_grade_handles (grade_level_id)"
        ))
