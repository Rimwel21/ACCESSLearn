# pyrefly: ignore [missing-import]
from sqlalchemy import inspect, text
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from database.connection import engine
from models.accounts import Accounts  # noqa: F401 - register audit log account foreign key
from models.audit_log import AuditLog  # noqa: F401 - register mapper relationships during startup
from models.HI_sections import HI_SECTIONS
from models.grade_levels import GradeLevels
from models.teacher_grade_handles import TeacherGradeHandles
from utils.enum import AccountStatusEnum, AuditActionEnum, SectionStatusEnum


def ensure_academic_tables() -> None:
    """Create legacy academic tables when an existing DB is missing them."""
    inspector = inspect(engine)

    if not inspector.has_table(GradeLevels.__tablename__):
        GradeLevels.__table__.create(bind=engine, checkfirst=True)

    inspector = inspect(engine)
    if not inspector.has_table(HI_SECTIONS.__tablename__):
        HI_SECTIONS.__table__.create(bind=engine, checkfirst=True)

    from models.teacher_section_assignments import TeacherSectionAssignment
    inspector = inspect(engine)
    if not inspector.has_table(TeacherSectionAssignment.__tablename__):
        TeacherSectionAssignment.__table__.create(bind=engine, checkfirst=True)

    _ensure_postgres_enum_values()
    _ensure_audit_log_schema()
    _ensure_teacher_grade_handles_schema()
    _ensure_teacher_assessments_schema()
    _ensure_student_profile_registration_schema()
    _ensure_hi_sections_teacher_id()
    _seed_default_academic_options()


def _ensure_hi_sections_teacher_id() -> None:
    """Add teacher_id column to hi_sections if missing (admin-assigned teacher)."""
    inspector = inspect(engine)
    if not inspector.has_table("hi_sections"):
        return

    columns = {col["name"] for col in inspector.get_columns("hi_sections")}
    if "teacher_id" in columns:
        return

    is_pg = engine.dialect.name == "postgresql"
    with engine.begin() as connection:
        if is_pg:
            connection.execute(text(
                "ALTER TABLE hi_sections "
                "ADD COLUMN IF NOT EXISTS teacher_id INTEGER REFERENCES accounts(id) ON DELETE SET NULL"
            ))
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_hi_sections_teacher_id ON hi_sections (teacher_id)"
            ))
        else:
            # SQLite: plain ALTER TABLE without IF NOT EXISTS support
            connection.execute(text(
                "ALTER TABLE hi_sections ADD COLUMN teacher_id INTEGER REFERENCES accounts(id)"
            ))




def _ensure_postgres_enum_values() -> None:
    if engine.dialect.name != "postgresql":
        return

    enum_values = {
        "accountstatusenum": [status.value for status in AccountStatusEnum],
        "auditactionenum": [action.value for action in AuditActionEnum],
    }

    with engine.begin() as connection:
        for enum_name, values in enum_values.items():
            for value in values:
                safe_value = value.replace("'", "''")
                connection.execute(text(
                    f"""
                    DO $$
                    BEGIN
                        IF EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN
                            ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{safe_value}';
                        END IF;
                    END $$;
                    """
                ))


def _ensure_audit_log_schema() -> None:
    inspector = inspect(engine)
    if not inspector.has_table(AuditLog.__tablename__):
        AuditLog.__table__.create(bind=engine, checkfirst=True)


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

    is_pg = engine.dialect.name == "postgresql"
    with engine.begin() as connection:
        if "grade_level_id" not in columns:
            if is_pg:
                connection.execute(text(
                    "ALTER TABLE teacher_grade_handles "
                    "ADD COLUMN IF NOT EXISTS grade_level_id INTEGER REFERENCES grade_levels(id)"
                ))
            else:
                connection.execute(text(
                    "ALTER TABLE teacher_grade_handles ADD COLUMN grade_level_id INTEGER REFERENCES grade_levels(id)"
                ))

        if is_pg and "grade_level_handles" in columns:
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

        if is_pg:
            connection.execute(text(
                "CREATE INDEX IF NOT EXISTS ix_teacher_grade_handles_grade_level_id "
                "ON teacher_grade_handles (grade_level_id)"
            ))


def _ensure_teacher_assessments_schema() -> None:
    inspector = inspect(engine)
    table_name = "teacher_assessments"

    if not inspector.has_table(table_name):
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}

    is_pg = engine.dialect.name == "postgresql"
    with engine.begin() as connection:
        if "due_at" not in columns:
            if is_pg:
                connection.execute(text(
                    "ALTER TABLE teacher_assessments "
                    "ADD COLUMN IF NOT EXISTS due_at TIMESTAMP WITH TIME ZONE"
                ))
            else:
                connection.execute(text(
                    "ALTER TABLE teacher_assessments ADD COLUMN due_at DATETIME"
                ))
        if "time_limit_seconds" not in columns:
            if is_pg:
                connection.execute(text(
                    "ALTER TABLE teacher_assessments "
                    "ADD COLUMN IF NOT EXISTS time_limit_seconds INTEGER"
                ))
            else:
                connection.execute(text(
                    "ALTER TABLE teacher_assessments ADD COLUMN time_limit_seconds INTEGER"
                ))
            rows = connection.execute(text(
                "SELECT id, time_limit FROM teacher_assessments WHERE time_limit IS NOT NULL"
            )).fetchall()
            for row in rows:
                seconds = _parse_time_limit_seconds(row.time_limit)
                if seconds:
                    connection.execute(
                        text("UPDATE teacher_assessments SET time_limit_seconds = :seconds WHERE id = :id"),
                        {"seconds": seconds, "id": row.id},
                    )

    _ensure_student_quiz_progress_schema()


def _ensure_student_quiz_progress_schema() -> None:
    inspector = inspect(engine)
    table_name = "student_quiz_progress"

    if not inspector.has_table(table_name):
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}

    is_pg = engine.dialect.name == "postgresql"
    with engine.begin() as connection:
        if "time_limit_seconds" not in columns:
            if is_pg:
                connection.execute(text(
                    "ALTER TABLE student_quiz_progress "
                    "ADD COLUMN IF NOT EXISTS time_limit_seconds INTEGER"
                ))
            else:
                connection.execute(text(
                    "ALTER TABLE student_quiz_progress ADD COLUMN time_limit_seconds INTEGER"
                ))
        if "expires_at" not in columns:
            if is_pg:
                connection.execute(text(
                    "ALTER TABLE student_quiz_progress "
                    "ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE"
                ))
            else:
                connection.execute(text(
                    "ALTER TABLE student_quiz_progress ADD COLUMN expires_at DATETIME"
                ))
        if "submission_type" not in columns:
            if is_pg:
                connection.execute(text(
                    "ALTER TABLE student_quiz_progress "
                    "ADD COLUMN IF NOT EXISTS submission_type VARCHAR(20)"
                ))
            else:
                connection.execute(text(
                    "ALTER TABLE student_quiz_progress ADD COLUMN submission_type VARCHAR(20)"
                ))
        if is_pg:
            connection.execute(text(
                "ALTER TABLE student_quiz_progress "
                "ALTER COLUMN started_at DROP NOT NULL"
            ))


def _parse_time_limit_seconds(value: str | None) -> int | None:
    if not value:
        return None
    parts = value.strip().lower().split()
    if not parts or not parts[0].isdigit():
        return None
    amount = int(parts[0])
    if amount <= 0:
        return None
    unit = parts[1] if len(parts) > 1 else "seconds"
    if unit.startswith("hour"):
        return amount * 3600
    if unit.startswith("minute"):
        return amount * 60
    if unit.startswith("second"):
        return amount
    return None


def _ensure_student_profile_registration_schema() -> None:
    inspector = inspect(engine)
    table_name = "student_profiles"

    if not inspector.has_table(table_name):
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}

    is_pg = engine.dialect.name == "postgresql"
    with engine.begin() as connection:
        if "student_lrn" not in columns:
            if is_pg:
                connection.execute(text(
                    "ALTER TABLE student_profiles "
                    "ADD COLUMN IF NOT EXISTS student_lrn VARCHAR(12)"
                ))
            else:
                connection.execute(text(
                    "ALTER TABLE student_profiles ADD COLUMN student_lrn VARCHAR(12)"
                ))

        if "accessibility_profile" not in columns:
            if is_pg:
                connection.execute(text(
                    "ALTER TABLE student_profiles "
                    "ADD COLUMN IF NOT EXISTS accessibility_profile VARCHAR"
                ))
            else:
                connection.execute(text(
                    "ALTER TABLE student_profiles ADD COLUMN accessibility_profile VARCHAR"
                ))

        if "learning_preferences" not in columns:
            if is_pg:
                connection.execute(text(
                    "ALTER TABLE student_profiles "
                    "ADD COLUMN IF NOT EXISTS learning_preferences VARCHAR"
                ))
            else:
                connection.execute(text(
                    "ALTER TABLE student_profiles ADD COLUMN learning_preferences VARCHAR"
                ))

        # PostgreSQL-only: partial unique index and FK migration via DO $$ block
        if is_pg:
            connection.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS ix_student_profiles_student_lrn "
                "ON student_profiles (student_lrn) WHERE student_lrn IS NOT NULL"
            ))
            connection.execute(text(
                """
                DO $$
                DECLARE
                    stale_fk_name TEXT;
                BEGIN
                    SELECT constraint_name INTO stale_fk_name
                    FROM information_schema.referential_constraints
                    WHERE constraint_schema = current_schema()
                      AND constraint_name IN (
                        SELECT tc.constraint_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name
                         AND tc.constraint_schema = kcu.constraint_schema
                        WHERE tc.table_name = 'student_profiles'
                          AND tc.constraint_type = 'FOREIGN KEY'
                          AND kcu.column_name = 'section_id'
                      )
                      AND unique_constraint_name IN (
                        SELECT constraint_name
                        FROM information_schema.table_constraints
                        WHERE table_name = 'sections'
                          AND constraint_type IN ('PRIMARY KEY', 'UNIQUE')
                      )
                    LIMIT 1;

                    IF stale_fk_name IS NOT NULL THEN
                        EXECUTE format('ALTER TABLE student_profiles DROP CONSTRAINT %I', stale_fk_name);
                    END IF;

                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage kcu
                          ON tc.constraint_name = kcu.constraint_name
                         AND tc.constraint_schema = kcu.constraint_schema
                        JOIN information_schema.referential_constraints rc
                          ON tc.constraint_name = rc.constraint_name
                         AND tc.constraint_schema = rc.constraint_schema
                        JOIN information_schema.table_constraints parent_tc
                          ON rc.unique_constraint_name = parent_tc.constraint_name
                         AND rc.unique_constraint_schema = parent_tc.constraint_schema
                        WHERE tc.table_name = 'student_profiles'
                          AND tc.constraint_type = 'FOREIGN KEY'
                          AND kcu.column_name = 'section_id'
                          AND parent_tc.table_name = 'hi_sections'
                    ) THEN
                        ALTER TABLE student_profiles
                        ADD CONSTRAINT student_profiles_section_id_fkey
                        FOREIGN KEY (section_id) REFERENCES hi_sections(id) NOT VALID;
                    END IF;
                END $$;
                """
            ))
