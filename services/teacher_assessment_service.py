from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session
from models.accounts import Accounts
from models.learning_topic import LearningTopic
from models.student_profile import StudentProfile
from models.student_quiz_progress import StudentQuizProgress
from models.teacher_assessment import TeacherAssessment
from models.teacher_class import TeacherClass
from models.teacher_module import TeacherModule
from schemas.teacher_assessment_schema import TeacherAssessmentCreate, TeacherAssessmentUpdate
from utils.enum import RoleEnum
from utils.options import ALLOWED_LEARNING_WEEKS


def _ensure_teacher(current_user: Accounts):
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")


def list_teacher_assessments(request: Request, assessment_type: str, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)
    if assessment_type not in {"quiz", "activity"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment type must be quiz or activity")

    assessments = (
        db.query(TeacherAssessment)
        .filter(
            TeacherAssessment.teacher_id == current_user.id,
            TeacherAssessment.assessment_type == assessment_type
        )
        .order_by(TeacherAssessment.created_at.desc())
        .all()
    )
    if assessment_type == "activity":
        return [_assessment_with_submissions(assessment, db) for assessment in assessments]
    return assessments


def create_teacher_assessment(request: Request, assessment: TeacherAssessmentCreate, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)
    _validate_assessment_assignment(assessment, db, current_user)
    _validate_week(assessment.week)

    new_assessment = TeacherAssessment(
        teacher_id=current_user.id,
        class_id=assessment.class_id,
        module_id=assessment.module_id,
        topic_id=assessment.topic_id,
        assessment_type=assessment.assessment_type,
        title=assessment.title.strip(),
        description=assessment.description.strip(),
        category=assessment.category.strip() if assessment.category else None,
        week=assessment.week.strip() if assessment.week else None,
        time_limit=assessment.time_limit.strip() if assessment.time_limit else None,
        attempts_allowed=assessment.attempts_allowed,
        shuffle_questions=str(assessment.shuffle_questions).lower(),
        show_answers_after_submission=str(assessment.show_answers_after_submission).lower(),
        questions=[question.model_dump() for question in assessment.questions],
        due_at=assessment.due_at,
    )

    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)

    return new_assessment


def update_teacher_assessment(request: Request, assessment_id: int, update: TeacherAssessmentUpdate, db: Session, current_user: Accounts):
    assessment = get_teacher_assessment(request, assessment_id, db, current_user)
    update_data = update.model_dump(exclude_unset=True)

    module_id = update_data.get("module_id", assessment.module_id)
    topic_id = update_data.get("topic_id", assessment.topic_id)
    class_id = update_data.get("class_id", assessment.class_id)
    assessment_type = update_data.get("assessment_type", assessment.assessment_type)
    if any(key in update_data for key in {"class_id", "module_id", "topic_id"}):
        _validate_assignment_values(assessment_type, class_id, module_id, topic_id, db, current_user)
    if "week" in update_data:
        _validate_week(update_data.get("week"))

    for key, value in update_data.items():
        if key in {"shuffle_questions", "show_answers_after_submission"} and isinstance(value, bool):
            setattr(assessment, key, str(value).lower())
        elif key == "questions" and value is not None:
            setattr(assessment, key, [question.model_dump() for question in update.questions or []])
        else:
            setattr(assessment, key, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(assessment)
    return assessment


def delete_teacher_assessment(request: Request, assessment_id: int, db: Session, current_user: Accounts):
    assessment = get_teacher_assessment(request, assessment_id, db, current_user)
    db.delete(assessment)
    db.commit()
    return {"detail": "Assessment deleted successfully"}


def get_teacher_assessment(request: Request, assessment_id: int, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)
    assessment = db.query(TeacherAssessment).filter(
        TeacherAssessment.id == assessment_id,
        TeacherAssessment.teacher_id == current_user.id,
    ).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return assessment


def _validate_module_topic(module_id: int | None, topic_id: int | None, db: Session, current_user: Accounts):
    if module_id is not None:
        module = db.query(TeacherModule).filter(
            TeacherModule.id == module_id,
            TeacherModule.teacher_id == current_user.id,
        ).first()
        if not module:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
        if module.class_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select a class-assigned learning material")
    elif module_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select a class-assigned learning material")

    if topic_id is not None:
        topic = db.query(LearningTopic).join(TeacherModule).filter(
            LearningTopic.id == topic_id,
            TeacherModule.teacher_id == current_user.id,
        ).first()
        if not topic:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")
        if module_id is not None and topic.module_id != module_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Topic does not belong to the selected module")


def _validate_week(week: str | None):
    if week is not None and week not in ALLOWED_LEARNING_WEEKS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Week must be one of: {', '.join(ALLOWED_LEARNING_WEEKS)}",
        )


def _validate_assessment_assignment(assessment: TeacherAssessmentCreate, db: Session, current_user: Accounts):
    _validate_assignment_values(
        assessment.assessment_type,
        assessment.class_id,
        assessment.module_id,
        assessment.topic_id,
        db,
        current_user,
    )


def _validate_assignment_values(
    assessment_type: str,
    class_id: int | None,
    module_id: int | None,
    topic_id: int | None,
    db: Session,
    current_user: Accounts,
):
    if assessment_type == "activity":
        if class_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select a target class")
        existing_class = db.query(TeacherClass.id).filter(
            TeacherClass.id == class_id,
            TeacherClass.teacher_id == current_user.id,
        ).first()
        if not existing_class:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        if module_id is not None or topic_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Activities are assigned directly to a class")
        return

    _validate_module_topic(module_id, topic_id, db, current_user)


def _assessment_with_submissions(assessment: TeacherAssessment, db: Session):
    submissions = (
        db.query(StudentQuizProgress, StudentProfile)
        .join(StudentProfile, StudentProfile.account_id == StudentQuizProgress.student_id)
        .filter(
            StudentQuizProgress.assessment_id == assessment.id,
            StudentQuizProgress.status == "completed",
        )
        .order_by(StudentQuizProgress.completed_at.desc())
        .all()
    )

    return {
        "id": assessment.id,
        "teacher_id": assessment.teacher_id,
        "class_id": assessment.class_id,
        "module_id": assessment.module_id,
        "topic_id": assessment.topic_id,
        "assessment_type": assessment.assessment_type,
        "title": assessment.title,
        "description": assessment.description,
        "category": assessment.category,
        "week": assessment.week,
        "time_limit": assessment.time_limit,
        "attempts_allowed": assessment.attempts_allowed,
        "shuffle_questions": _string_to_bool(assessment.shuffle_questions),
        "show_answers_after_submission": _string_to_bool(assessment.show_answers_after_submission),
        "questions": assessment.questions or [],
        "due_at": assessment.due_at,
        "submissions_count": len(submissions),
        "submissions": [
            {
                "id": progress.id,
                "student_id": progress.student_id,
                "student_name": student.name,
                "score": progress.score,
                "total": progress.total,
                "answers": progress.answers or {},
                "completed_at": progress.completed_at,
            }
            for progress, student in submissions
        ],
        "created_at": assessment.created_at,
        "updated_at": assessment.updated_at,
    }


def _string_to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}
