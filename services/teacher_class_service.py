from fastapi import HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from models.accounts import Accounts
from models.learning_topic import LearningTopic
from models.student_progress import StudentTopicProgress
from models.student_profile import StudentProfile
from models.student_quiz_progress import StudentQuizProgress
from models.teacher_assessment import TeacherAssessment
from models.teacher_class import TeacherClass
from models.teacher_module import TeacherModule
from models.grade_levels import GradeLevels
from models.HI_sections import HI_SECTIONS
from schemas.teacher_class_schema import TeacherClassCreate
from services.academic_service import get_grade_level_or_404, get_section_for_grade_or_400
from utils.enum import RoleEnum


def _ensure_teacher(current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")


def list_teacher_classes(request: Request, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    classes = (
        db.query(TeacherClass)
        .options(
            joinedload(TeacherClass.grade_levels),
            joinedload(TeacherClass.sections)
        )
        .join(GradeLevels, TeacherClass.grade_level_id == GradeLevels.id)
        .join(HI_SECTIONS, TeacherClass.section_id == HI_SECTIONS.id)
        .filter(TeacherClass.teacher_id == current_user.id)
        .order_by(TeacherClass.created_at.desc())
        .all()
    )
    for teacher_class in classes:
        teacher_class.student_count = _count_matching_students(teacher_class, db)
    return classes


def create_teacher_class(request: Request, teacher_class: TeacherClassCreate, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    get_grade_level_or_404(teacher_class.grade_level_id, db)
    get_section_for_grade_or_400(teacher_class.section_id, teacher_class.grade_level_id, db)

    new_teacher_class = TeacherClass(
        teacher_id=current_user.id,
        class_name=teacher_class.class_name.strip(),
        subject=teacher_class.subject.strip(),
        grade_level_id=teacher_class.grade_level_id,
        section_id=teacher_class.section_id,
        school_year=teacher_class.school_year.strip() if teacher_class.school_year else None,
    )

    db.add(new_teacher_class)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Class already exists for this teacher, subject, grade level, and section"
        )

    db.refresh(new_teacher_class)
    new_teacher_class.student_count = _count_matching_students(new_teacher_class, db)

    result = (
        db.query(TeacherClass)
        .options(
            joinedload(TeacherClass.grade_levels),
            joinedload(TeacherClass.sections)
        )
        .filter(TeacherClass.id == new_teacher_class.id)
        .first()
        )

    return result


def get_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)

    teacher_class = (
        db.query(TeacherClass)
        .options(
            joinedload(TeacherClass.grade_levels),
            joinedload(TeacherClass.sections)
        )
        .join(GradeLevels, TeacherClass.grade_level_id == GradeLevels.id)
        .join(HI_SECTIONS, TeacherClass.section_id == HI_SECTIONS.id)
        .filter(TeacherClass.id == class_id, TeacherClass.teacher_id == current_user.id)
        .first()
    )

    if not teacher_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    teacher_class.student_count = _count_matching_students(teacher_class, db)
    return teacher_class


def delete_teacher_class(request: Request, class_id: int, db: Session, current_user: Accounts):
    teacher_class = get_teacher_class(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user
    )

    db.delete(teacher_class)
    db.commit()

    return {"detail": "Class deleted successfully"}


def list_class_students(request: Request, class_id: int, db: Session, current_user: Accounts):
    teacher_class = get_teacher_class(
        request=request,
        class_id=class_id,
        db=db,
        current_user=current_user
    )

    return _matching_student_query(teacher_class, db).all()


def get_teacher_dashboard_summary(request: Request, class_id: int | None, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)
    if class_id is None:
        classes = (
            db.query(TeacherClass)
            .filter(TeacherClass.teacher_id == current_user.id)
            .all()
        )
    else:
        classes = [get_teacher_class(request=request, class_id=class_id, db=db, current_user=current_user)]
    students = _unique_students_for_classes(classes, db)
    student_ids = [student.account_id for student in students]
    module_count_filters = [
        TeacherModule.teacher_id == current_user.id,
        TeacherModule.status == "Published",
    ]
    if class_id is not None:
        module_count_filters.append(TeacherModule.class_id == class_id)
    published_module_count = db.query(TeacherModule).filter(*module_count_filters).count()

    quiz_average = _average_quiz_score(student_ids, [teacher_class.id for teacher_class in classes], db, current_user)
    student_progress = [
        _dashboard_progress_for_student(student, classes, db, current_user)
        for student in students
    ]

    return {
        "total_students": len(students),
        "active_learning_materials": published_module_count,
        "average_quiz_score": quiz_average,
        "student_progress": student_progress,
    }


def list_recent_activities(request: Request, limit: int, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)
    classes = db.query(TeacherClass).filter(TeacherClass.teacher_id == current_user.id).all()
    class_ids = [teacher_class.id for teacher_class in classes]
    if not class_ids:
        return []

    topic_rows = (
        db.query(StudentTopicProgress, StudentProfile, TeacherModule, LearningTopic)
        .join(LearningTopic, LearningTopic.id == StudentTopicProgress.topic_id)
        .join(TeacherModule, TeacherModule.id == StudentTopicProgress.module_id)
        .join(StudentProfile, StudentProfile.account_id == StudentTopicProgress.student_id)
        .filter(
            TeacherModule.teacher_id == current_user.id,
            TeacherModule.class_id.in_(class_ids),
            StudentTopicProgress.status == "completed",
            StudentTopicProgress.completed_at.isnot(None),
        )
        .all()
    )
    quiz_rows = (
        db.query(StudentQuizProgress, StudentProfile, TeacherAssessment)
        .join(TeacherAssessment, TeacherAssessment.id == StudentQuizProgress.assessment_id)
        .join(StudentProfile, StudentProfile.account_id == StudentQuizProgress.student_id)
        .outerjoin(TeacherModule, TeacherModule.id == TeacherAssessment.module_id)
        .filter(
            TeacherAssessment.teacher_id == current_user.id,
            StudentQuizProgress.status == "completed",
            StudentQuizProgress.completed_at.isnot(None),
            or_(
                TeacherAssessment.class_id.in_(class_ids),
                TeacherModule.class_id.in_(class_ids),
            ),
        )
        .all()
    )

    activities = []
    for progress, student, module, topic in topic_rows:
        activities.append({
            "id": f"topic-{progress.id}",
            "text": f"{student.name} completed {topic.title} in {module.title}",
            "occurred_at": progress.completed_at,
            "activity_type": "material",
        })
    for progress, student, assessment in quiz_rows:
        label = "quiz" if assessment.assessment_type == "quiz" else "activity"
        score = f" ({progress.score}/{progress.total})" if progress.total else ""
        activities.append({
            "id": f"{assessment.assessment_type}-{progress.id}",
            "text": f"{student.name} completed {label} {assessment.title}{score}",
            "occurred_at": progress.completed_at,
            "activity_type": assessment.assessment_type,
        })

    activities.sort(key=lambda item: item["occurred_at"], reverse=True)
    return activities[:limit]


def _matching_student_query(teacher_class: TeacherClass, db: Session):
    return (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.grade_level),
            joinedload(StudentProfile.section)
        )
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .filter(
            StudentProfile.grade_level_id == teacher_class.grade_level_id,
            StudentProfile.section_id == teacher_class.section_id,
            Accounts.role == RoleEnum.student,
        )
        .order_by(StudentProfile.name.asc())
    )


def _count_matching_students(teacher_class: TeacherClass, db: Session):
    return _matching_student_query(teacher_class, db).count()


def _unique_students_for_classes(classes: list[TeacherClass], db: Session):
    filters = []
    for teacher_class in classes:
        filters.append(
            (
                StudentProfile.grade_level_id == teacher_class.grade_level_id
            ) & (
                StudentProfile.section_id == teacher_class.section_id
            )
        )
    if not filters:
        return []

    return (
        db.query(StudentProfile)
        .join(Accounts, Accounts.id == StudentProfile.account_id)
        .filter(Accounts.role == RoleEnum.student, or_(*filters))
        .order_by(StudentProfile.name.asc())
        .all()
    )


def _average_quiz_score(student_ids: list[int], class_ids: list[int], db: Session, current_user: Accounts):
    if not student_ids:
        return 0
    module_ids = [
        row.id for row in db.query(TeacherModule.id)
        .filter(
            TeacherModule.teacher_id == current_user.id,
            TeacherModule.class_id.in_(class_ids),
        )
        .all()
    ] if class_ids else []
    quiz_rows = (
        db.query(StudentQuizProgress.score, StudentQuizProgress.total)
        .join(TeacherAssessment, TeacherAssessment.id == StudentQuizProgress.assessment_id)
        .filter(
            TeacherAssessment.teacher_id == current_user.id,
            TeacherAssessment.assessment_type == "quiz",
            TeacherAssessment.module_id.in_(module_ids),
            StudentQuizProgress.student_id.in_(student_ids),
            StudentQuizProgress.status == "completed",
            StudentQuizProgress.total.isnot(None),
            StudentQuizProgress.total > 0,
        )
        .all()
    )
    if not quiz_rows:
        return 0
    percentages = [(row.score or 0) / row.total * 100 for row in quiz_rows]
    return round(sum(percentages) / len(percentages))


def _dashboard_progress_for_student(student: StudentProfile, classes: list[TeacherClass], db: Session, current_user: Accounts):
    matching_class_ids = [
        teacher_class.id for teacher_class in classes
        if teacher_class.grade_level_id == student.grade_level_id
        and teacher_class.section_id == student.section_id
    ]
    if not matching_class_ids:
        total_items = 0
        completed_items = 0
        topic_ids = []
        activity_ids = []
        completed_topic_ids = set()
        in_progress_topic_ids = set()
        completed_activity_ids = set()
        last_activity = None
        quiz_activity = None
    else:
        module_ids = [
            row.id for row in db.query(TeacherModule.id)
            .filter(
                TeacherModule.teacher_id == current_user.id,
                TeacherModule.class_id.in_(matching_class_ids),
                TeacherModule.status == "Published",
            )
            .all()
        ]
        topic_ids = [
            row.id for row in db.query(LearningTopic.id)
            .filter(LearningTopic.module_id.in_(module_ids))
            .all()
        ] if module_ids else []
        quiz_ids = [
            row.id for row in db.query(TeacherAssessment.id)
            .filter(
                TeacherAssessment.teacher_id == current_user.id,
                TeacherAssessment.module_id.in_(module_ids),
                TeacherAssessment.assessment_type == "quiz",
            )
            .all()
        ] if module_ids else []
        activity_ids = [
            row.id for row in db.query(TeacherAssessment.id)
            .filter(
                TeacherAssessment.teacher_id == current_user.id,
                TeacherAssessment.class_id.in_(matching_class_ids),
                TeacherAssessment.assessment_type == "activity",
            )
            .all()
        ]

        topic_progress = db.query(StudentTopicProgress).filter(
            StudentTopicProgress.student_id == student.account_id,
            StudentTopicProgress.topic_id.in_(topic_ids),
        ).all() if topic_ids else []
        quiz_progress = db.query(StudentQuizProgress).filter(
            StudentQuizProgress.student_id == student.account_id,
            StudentQuizProgress.assessment_id.in_(quiz_ids),
        ).all() if quiz_ids else []
        activity_progress = db.query(StudentQuizProgress).filter(
            StudentQuizProgress.student_id == student.account_id,
            StudentQuizProgress.assessment_id.in_(activity_ids),
        ).all() if activity_ids else []

        completed_topic_ids = {item.topic_id for item in topic_progress if item.status == "completed"}
        in_progress_topic_ids = {item.topic_id for item in topic_progress if item.status in {"started", "in_progress"}}
        completed_quiz_ids = {item.assessment_id for item in quiz_progress if item.status == "completed"}
        completed_activity_ids = {item.assessment_id for item in activity_progress if item.status == "completed"}
        total_items = len(topic_ids) + len(quiz_ids) + len(activity_ids)
        completed_items = len(completed_topic_ids) + len(completed_quiz_ids) + len(completed_activity_ids)
        activity_dates = [item.updated_at for item in topic_progress + quiz_progress + activity_progress if item.updated_at]
        last_activity = max(activity_dates) if activity_dates else None
        latest_quiz_progress = max(
            (item for item in quiz_progress if item.updated_at),
            key=lambda item: item.updated_at,
            default=None,
        )
        quiz_activity = _format_quiz_activity(latest_quiz_progress, db) if latest_quiz_progress else None

    status_percent = round((completed_items / total_items) * 100) if total_items else 0
    learning_material_percent = round((len(completed_topic_ids) / len(topic_ids)) * 100) if topic_ids else 0
    activity_percent = round((len(completed_activity_ids) / len(activity_ids)) * 100) if activity_ids else 0
    status_value = "Complete" if total_items and completed_items == total_items else "Needs Help" if status_percent < 50 else "In Progress"
    return {
        "student_id": student.account_id,
        "student_name": student.name,
        "overall_percent": learning_material_percent,
        "activities_completed": len(completed_activity_ids),
        "activities_total": len(activity_ids),
        "activity_percent": activity_percent,
        "learning_materials_completed": len(completed_topic_ids),
        "learning_materials_in_progress": len(in_progress_topic_ids),
        "learning_materials_total": len(topic_ids),
        "status": status_value,
        "last_activity": last_activity,
        "quiz_activity": quiz_activity,
    }


def _format_quiz_activity(progress: StudentQuizProgress, db: Session):
    assessment = db.query(TeacherAssessment).filter(TeacherAssessment.id == progress.assessment_id).first()
    if not assessment:
        return None
    if progress.total:
        return f"{assessment.title}: {progress.score or 0}/{progress.total}"
    return assessment.title


