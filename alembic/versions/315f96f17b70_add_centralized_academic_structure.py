"""add_centralized_academic_structure

Revision ID: 315f96f17b70
Revises: 7dac31640e29
Create Date: 2026-07-11 14:39:08.292490

"""
from typing import Sequence, Union

from alembic import op
from alembic import context
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '315f96f17b70'
down_revision: Union[str, Sequence[str], None] = '7dac31640e29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_foreign_key(inspector, table_name: str, constrained_columns: list[str], referred_table: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return any(
        foreign_key.get("constrained_columns") == constrained_columns
        and foreign_key.get("referred_table") == referred_table
        for foreign_key in inspector.get_foreign_keys(table_name)
    )


def _upgrade_offline(section_status: postgresql.ENUM) -> None:
    op.alter_column('grade_levels', 'name',
               existing_type=sa.String(length=20),
               type_=sa.String(length=100),
               existing_nullable=False)
    op.add_column('grade_levels', sa.Column('status', section_status, server_default='active', nullable=False))
    op.alter_column('grade_levels', 'status', server_default=None)
    op.add_column('grade_levels', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.alter_column('grade_levels', 'created_at', server_default=None)
    op.add_column('grade_levels', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.alter_column('grade_levels', 'updated_at', server_default=None)
    op.create_index(op.f('ix_grade_levels_status'), 'grade_levels', ['status'], unique=False)

    op.create_table('school_years',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('is_current', sa.Boolean(), nullable=False),
    sa.Column('status', section_status, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_school_years_id'), 'school_years', ['id'], unique=False)
    op.create_index(op.f('ix_school_years_status'), 'school_years', ['status'], unique=False)

    op.create_table('sections',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('capacity', sa.Integer(), nullable=False),
    sa.Column('subject', sa.String(length=100), nullable=True),
    sa.Column('status', section_status, nullable=False),
    sa.Column('grade_level_id', sa.Integer(), nullable=False),
    sa.Column('school_year_id', sa.Integer(), nullable=True),
    sa.Column('teacher_id', sa.Integer(), nullable=True),
    sa.Column('created_by', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['created_by'], ['accounts.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['grade_level_id'], ['grade_levels.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['school_year_id'], ['school_years.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['teacher_id'], ['accounts.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sections_grade_level_id'), 'sections', ['grade_level_id'], unique=False)
    op.create_index(op.f('ix_sections_id'), 'sections', ['id'], unique=False)
    op.create_index(op.f('ix_sections_school_year_id'), 'sections', ['school_year_id'], unique=False)
    op.create_index(op.f('ix_sections_status'), 'sections', ['status'], unique=False)
    op.create_index(op.f('ix_sections_teacher_id'), 'sections', ['teacher_id'], unique=False)

    op.create_table('teacher_assignment_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('section_id', sa.Integer(), nullable=False),
    sa.Column('previous_teacher_id', sa.Integer(), nullable=True),
    sa.Column('new_teacher_id', sa.Integer(), nullable=True),
    sa.Column('assigned_by', sa.Integer(), nullable=True),
    sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['assigned_by'], ['accounts.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['new_teacher_id'], ['accounts.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['previous_teacher_id'], ['accounts.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_teacher_assignment_history_id'), 'teacher_assignment_history', ['id'], unique=False)
    op.create_index(op.f('ix_teacher_assignment_history_new_teacher_id'), 'teacher_assignment_history', ['new_teacher_id'], unique=False)
    op.create_index(op.f('ix_teacher_assignment_history_previous_teacher_id'), 'teacher_assignment_history', ['previous_teacher_id'], unique=False)
    op.create_index(op.f('ix_teacher_assignment_history_section_id'), 'teacher_assignment_history', ['section_id'], unique=False)

    op.alter_column('student_profiles', 'age',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('student_profiles', 'sex',
               existing_type=postgresql.ENUM('Male', 'Female', name='usersex'),
               nullable=True)
    op.alter_column('student_profiles', 'student_type',
               existing_type=postgresql.ENUM('regular', 'HI', name='studenttype'),
               nullable=True)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    section_status = postgresql.ENUM('active', 'archived', name='sectionstatusenum', create_type=False)
    section_status.create(bind, checkfirst=True)
    if context.is_offline_mode():
        _upgrade_offline(section_status)
        return
    inspector = sa.inspect(bind)

    if not _has_table(inspector, 'grade_levels'):
        op.create_table('grade_levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('status', section_status, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
        )
    else:
        op.alter_column('grade_levels', 'name',
                   existing_type=sa.String(length=20),
                   type_=sa.String(length=100),
                   existing_nullable=False)
        if not _has_column(inspector, 'grade_levels', 'status'):
            op.add_column('grade_levels', sa.Column('status', section_status, server_default='active', nullable=False))
            op.alter_column('grade_levels', 'status', server_default=None)
        if not _has_column(inspector, 'grade_levels', 'created_at'):
            op.add_column('grade_levels', sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
            op.alter_column('grade_levels', 'created_at', server_default=None)
        if not _has_column(inspector, 'grade_levels', 'updated_at'):
            op.add_column('grade_levels', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
            op.alter_column('grade_levels', 'updated_at', server_default=None)
    inspector = sa.inspect(bind)
    if not _has_index(inspector, 'grade_levels', 'ix_grade_levels_id'):
        op.create_index(op.f('ix_grade_levels_id'), 'grade_levels', ['id'], unique=False)
    if not _has_index(inspector, 'grade_levels', 'ix_grade_levels_status'):
        op.create_index(op.f('ix_grade_levels_status'), 'grade_levels', ['status'], unique=False)

    if not _has_table(inspector, 'school_years'):
        op.create_table('school_years',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('status', section_status, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, 'school_years', 'ix_school_years_id'):
        op.create_index(op.f('ix_school_years_id'), 'school_years', ['id'], unique=False)
    if not _has_index(inspector, 'school_years', 'ix_school_years_status'):
        op.create_index(op.f('ix_school_years_status'), 'school_years', ['status'], unique=False)

    if not _has_table(inspector, 'sections'):
        op.create_table('sections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(length=100), nullable=True),
        sa.Column('status', section_status, nullable=False),
        sa.Column('grade_level_id', sa.Integer(), nullable=False),
        sa.Column('school_year_id', sa.Integer(), nullable=True),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['grade_level_id'], ['grade_levels.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_year_id'], ['school_years.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['teacher_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, 'sections', 'ix_sections_grade_level_id'):
        op.create_index(op.f('ix_sections_grade_level_id'), 'sections', ['grade_level_id'], unique=False)
    if not _has_index(inspector, 'sections', 'ix_sections_id'):
        op.create_index(op.f('ix_sections_id'), 'sections', ['id'], unique=False)
    if not _has_index(inspector, 'sections', 'ix_sections_school_year_id'):
        op.create_index(op.f('ix_sections_school_year_id'), 'sections', ['school_year_id'], unique=False)
    if not _has_index(inspector, 'sections', 'ix_sections_status'):
        op.create_index(op.f('ix_sections_status'), 'sections', ['status'], unique=False)
    if not _has_index(inspector, 'sections', 'ix_sections_teacher_id'):
        op.create_index(op.f('ix_sections_teacher_id'), 'sections', ['teacher_id'], unique=False)

    if not _has_table(inspector, 'teacher_assignment_history'):
        op.create_table('teacher_assignment_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('section_id', sa.Integer(), nullable=False),
        sa.Column('previous_teacher_id', sa.Integer(), nullable=True),
        sa.Column('new_teacher_id', sa.Integer(), nullable=True),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by'], ['accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['new_teacher_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['previous_teacher_id'], ['accounts.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, 'teacher_assignment_history', 'ix_teacher_assignment_history_id'):
        op.create_index(op.f('ix_teacher_assignment_history_id'), 'teacher_assignment_history', ['id'], unique=False)
    if not _has_index(inspector, 'teacher_assignment_history', 'ix_teacher_assignment_history_new_teacher_id'):
        op.create_index(op.f('ix_teacher_assignment_history_new_teacher_id'), 'teacher_assignment_history', ['new_teacher_id'], unique=False)
    if not _has_index(inspector, 'teacher_assignment_history', 'ix_teacher_assignment_history_previous_teacher_id'):
        op.create_index(op.f('ix_teacher_assignment_history_previous_teacher_id'), 'teacher_assignment_history', ['previous_teacher_id'], unique=False)
    if not _has_index(inspector, 'teacher_assignment_history', 'ix_teacher_assignment_history_section_id'):
        op.create_index(op.f('ix_teacher_assignment_history_section_id'), 'teacher_assignment_history', ['section_id'], unique=False)

    if not _has_column(inspector, 'student_profiles', 'grade_level_id'):
        op.add_column('student_profiles', sa.Column('grade_level_id', sa.Integer(), nullable=True))
    if not _has_column(inspector, 'student_profiles', 'section_id'):
        op.add_column('student_profiles', sa.Column('section_id', sa.Integer(), nullable=True))
    if _has_column(inspector, 'student_profiles', 'age'):
        op.alter_column('student_profiles', 'age',
                   existing_type=sa.INTEGER(),
                   nullable=True)
    if _has_column(inspector, 'student_profiles', 'sex'):
        op.alter_column('student_profiles', 'sex',
                   existing_type=postgresql.ENUM('Male', 'Female', name='usersex'),
                   nullable=True)
    if _has_column(inspector, 'student_profiles', 'student_type'):
        op.alter_column('student_profiles', 'student_type',
                   existing_type=postgresql.ENUM('regular', 'HI', name='studenttype'),
                   nullable=True)
    if _has_column(inspector, 'student_profiles', 'grade_level'):
        op.alter_column('student_profiles', 'grade_level',
                   existing_type=postgresql.ENUM('grade_1', 'grade_2', 'grade_3', 'grade_4', 'grade_5', 'grade_6', name='gradelevel'),
                   type_=sa.String(length=100),
                   nullable=True)
    if _has_column(inspector, 'student_profiles', 'section'):
        op.alter_column('student_profiles', 'section',
                   existing_type=sa.VARCHAR(length=250),
                   nullable=True)
    inspector = sa.inspect(bind)
    if not _has_index(inspector, 'student_profiles', 'ix_student_profiles_grade_level_id'):
        op.create_index(op.f('ix_student_profiles_grade_level_id'), 'student_profiles', ['grade_level_id'], unique=False)
    if not _has_index(inspector, 'student_profiles', 'ix_student_profiles_section_id'):
        op.create_index(op.f('ix_student_profiles_section_id'), 'student_profiles', ['section_id'], unique=False)
    if not _has_foreign_key(inspector, 'student_profiles', ['grade_level_id'], 'grade_levels'):
        op.create_foreign_key('fk_student_profiles_grade_level_id_grade_levels', 'student_profiles', 'grade_levels', ['grade_level_id'], ['id'], ondelete='SET NULL')
    if not _has_foreign_key(inspector, 'student_profiles', ['section_id'], 'sections') and not _has_foreign_key(inspector, 'student_profiles', ['section_id'], 'hi_sections'):
        op.create_foreign_key('fk_student_profiles_section_id_sections', 'student_profiles', 'sections', ['section_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    op.execute('ALTER TABLE student_profiles DROP CONSTRAINT IF EXISTS fk_student_profiles_section_id_sections')

    if _has_table(inspector, 'student_profiles'):
        if _has_column(inspector, 'student_profiles', 'section'):
            op.alter_column('student_profiles', 'section',
                       existing_type=sa.VARCHAR(length=250),
                       nullable=False)
        if _has_column(inspector, 'student_profiles', 'grade_level'):
            op.alter_column('student_profiles', 'grade_level',
                       existing_type=sa.String(length=100),
                       type_=postgresql.ENUM('grade_1', 'grade_2', 'grade_3', 'grade_4', 'grade_5', 'grade_6', name='gradelevel'),
                       nullable=False)
        if _has_column(inspector, 'student_profiles', 'student_type'):
            op.alter_column('student_profiles', 'student_type',
                       existing_type=postgresql.ENUM('regular', 'HI', name='studenttype'),
                       nullable=False)
        if _has_column(inspector, 'student_profiles', 'sex'):
            op.alter_column('student_profiles', 'sex',
                       existing_type=postgresql.ENUM('Male', 'Female', name='usersex'),
                       nullable=False)
        if _has_column(inspector, 'student_profiles', 'age'):
            op.alter_column('student_profiles', 'age',
                       existing_type=sa.INTEGER(),
                       nullable=False)

    inspector = sa.inspect(bind)
    if _has_table(inspector, 'teacher_assignment_history'):
        if _has_index(inspector, 'teacher_assignment_history', 'ix_teacher_assignment_history_section_id'):
            op.drop_index(op.f('ix_teacher_assignment_history_section_id'), table_name='teacher_assignment_history')
        if _has_index(inspector, 'teacher_assignment_history', 'ix_teacher_assignment_history_previous_teacher_id'):
            op.drop_index(op.f('ix_teacher_assignment_history_previous_teacher_id'), table_name='teacher_assignment_history')
        if _has_index(inspector, 'teacher_assignment_history', 'ix_teacher_assignment_history_new_teacher_id'):
            op.drop_index(op.f('ix_teacher_assignment_history_new_teacher_id'), table_name='teacher_assignment_history')
        if _has_index(inspector, 'teacher_assignment_history', 'ix_teacher_assignment_history_id'):
            op.drop_index(op.f('ix_teacher_assignment_history_id'), table_name='teacher_assignment_history')
        op.drop_table('teacher_assignment_history')

    inspector = sa.inspect(bind)
    if _has_table(inspector, 'sections'):
        if _has_index(inspector, 'sections', 'ix_sections_teacher_id'):
            op.drop_index(op.f('ix_sections_teacher_id'), table_name='sections')
        if _has_index(inspector, 'sections', 'ix_sections_status'):
            op.drop_index(op.f('ix_sections_status'), table_name='sections')
        if _has_index(inspector, 'sections', 'ix_sections_school_year_id'):
            op.drop_index(op.f('ix_sections_school_year_id'), table_name='sections')
        if _has_index(inspector, 'sections', 'ix_sections_id'):
            op.drop_index(op.f('ix_sections_id'), table_name='sections')
        if _has_index(inspector, 'sections', 'ix_sections_grade_level_id'):
            op.drop_index(op.f('ix_sections_grade_level_id'), table_name='sections')
        op.drop_table('sections')

    inspector = sa.inspect(bind)
    if _has_table(inspector, 'school_years'):
        if _has_index(inspector, 'school_years', 'ix_school_years_status'):
            op.drop_index(op.f('ix_school_years_status'), table_name='school_years')
        if _has_index(inspector, 'school_years', 'ix_school_years_id'):
            op.drop_index(op.f('ix_school_years_id'), table_name='school_years')
        op.drop_table('school_years')

    inspector = sa.inspect(bind)
    if _has_table(inspector, 'grade_levels'):
        if _has_index(inspector, 'grade_levels', 'ix_grade_levels_status'):
            op.drop_index(op.f('ix_grade_levels_status'), table_name='grade_levels')
        if _has_column(inspector, 'grade_levels', 'updated_at'):
            op.drop_column('grade_levels', 'updated_at')
        if _has_column(inspector, 'grade_levels', 'created_at'):
            op.drop_column('grade_levels', 'created_at')
        if _has_column(inspector, 'grade_levels', 'status'):
            op.drop_column('grade_levels', 'status')
        op.alter_column('grade_levels', 'name',
                   existing_type=sa.String(length=100),
                   type_=sa.String(length=20),
                   existing_nullable=False)
