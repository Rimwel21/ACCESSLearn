from pathlib import Path
from fastapi import HTTPException, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from models.accounts import Accounts
from models.learning_topic import LearningTopic
from models.student_quiz_progress import StudentQuizProgress
from models.student_progress import StudentTopicProgress
from models.student_profile import StudentProfile
from models.teacher_assessment import TeacherAssessment
from models.teacher_class import TeacherClass
from models.teacher_module import TeacherModule
from services.teacher_module_service import _extract_pdf_logical_topics, _needs_pdf_topic_regeneration, _replace_topic_records
from utils.enum import RoleEnum
from utils.utc_now import utc_now


def _ensure_student(current_user: Accounts):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student only")


def list_student_modules(request: Request, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        return []
    grade_level = _grade_value(profile.grade_level)
    section = _normalize_section(profile.section)

    modules = (
        db.query(TeacherModule)
        .join(TeacherClass, TeacherClass.id == TeacherModule.class_id)
        .options(joinedload(TeacherModule.topics), joinedload(TeacherModule.assessments))
        .filter(
            TeacherModule.status == "Published",
            TeacherClass.grade_level == grade_level,
            func.lower(func.trim(TeacherClass.section)) == section.lower(),
        )
        .order_by(TeacherModule.created_at.asc())
        .all()
    )
    _ensure_topics(db, modules)
    return modules


def list_student_activities(request: Request, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        return []
    grade_level = _grade_value(profile.grade_level)
    section = _normalize_section(profile.section)

    return (
        db.query(TeacherAssessment)
        .join(TeacherClass, TeacherClass.id == TeacherAssessment.class_id)
        .filter(
            TeacherAssessment.assessment_type == "activity",
            TeacherAssessment.class_id.isnot(None),
            TeacherClass.grade_level == grade_level,
            func.lower(func.trim(TeacherClass.section)) == section.lower(),
        )
        .order_by(TeacherAssessment.created_at.asc())
        .all()
    )


def get_student_activity(request: Request, activity_id: int, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    grade_level = _grade_value(profile.grade_level)
    section = _normalize_section(profile.section)

    activity = (
        db.query(TeacherAssessment)
        .join(TeacherClass, TeacherClass.id == TeacherAssessment.class_id)
        .filter(
            TeacherAssessment.id == activity_id,
            TeacherAssessment.assessment_type == "activity",
            TeacherAssessment.class_id.isnot(None),
            TeacherClass.grade_level == grade_level,
            func.lower(func.trim(TeacherClass.section)) == section.lower(),
        )
        .first()
    )
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return activity


def get_student_module(request: Request, module_id: int, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    grade_level = _grade_value(profile.grade_level)
    section = _normalize_section(profile.section)

    module = (
        db.query(TeacherModule)
        .join(TeacherClass, TeacherClass.id == TeacherModule.class_id)
        .options(joinedload(TeacherModule.topics), joinedload(TeacherModule.assessments))
        .filter(
            TeacherModule.id == module_id,
            TeacherModule.status == "Published",
            TeacherClass.grade_level == grade_level,
            func.lower(func.trim(TeacherClass.section)) == section.lower(),
        )
        .first()
    )
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    _ensure_topics(db, [module])
    module.topics.sort(key=lambda topic: topic.sort_order)
    return module


def get_module_progress(request: Request, module_id: int, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    _ensure_enrolled_module(module_id, db, current_user)
    topic_ids = [
        topic.id for topic in db.query(LearningTopic.id)
        .join(TeacherModule, TeacherModule.id == LearningTopic.module_id)
        .filter(TeacherModule.id == module_id, TeacherModule.status == "Published")
        .all()
    ]
    quiz_ids = [
        row.id for row in db.query(TeacherAssessment.id)
        .filter(
            TeacherAssessment.module_id == module_id,
            TeacherAssessment.assessment_type == "quiz",
        )
        .all()
    ]
    completed_ids = [
        row.topic_id for row in db.query(StudentTopicProgress.topic_id)
        .filter(
            StudentTopicProgress.student_id == current_user.id,
            StudentTopicProgress.module_id == module_id,
            StudentTopicProgress.status == "completed",
        )
        .all()
    ]
    completed_quiz_ids = [
        row.assessment_id for row in db.query(StudentQuizProgress.assessment_id)
        .filter(
            StudentQuizProgress.student_id == current_user.id,
            StudentQuizProgress.module_id == module_id,
            StudentQuizProgress.status == "completed",
        )
        .all()
    ]
    completed = len(set(completed_ids) & set(topic_ids))
    total = len(topic_ids)
    completed_quizzes = len(set(completed_quiz_ids) & set(quiz_ids))
    total_quizzes = len(quiz_ids)
    total_items = total + total_quizzes
    completed_items = completed + completed_quizzes
    return {
        "completed_topic_ids": completed_ids,
        "completed_quiz_ids": completed_quiz_ids,
        "total_topics": total,
        "completed_topics": completed,
        "total_quizzes": total_quizzes,
        "completed_quizzes": completed_quizzes,
        "percent": round((completed_items / total_items) * 100) if total_items else 0,
    }


def update_topic_progress(request: Request, module_id: int, topic_id: int, status_value: str, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    _ensure_enrolled_module(module_id, db, current_user)
    if status_value not in {"started", "in_progress", "completed"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid progress status")

    topic = (
        db.query(LearningTopic)
        .join(TeacherModule, TeacherModule.id == LearningTopic.module_id)
        .filter(LearningTopic.id == topic_id, LearningTopic.module_id == module_id, TeacherModule.status == "Published")
        .first()
    )
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    progress = db.query(StudentTopicProgress).filter(
        StudentTopicProgress.student_id == current_user.id,
        StudentTopicProgress.topic_id == topic_id,
    ).first()

    if not progress:
        progress = StudentTopicProgress(
            student_id=current_user.id,
            module_id=module_id,
            topic_id=topic_id,
            status=status_value,
        )
        db.add(progress)
    else:
        progress.status = status_value

    if status_value == "completed":
        progress.completed_at = utc_now()

    db.commit()
    return get_module_progress(request, module_id, db, current_user)


def submit_quiz_progress(request: Request, module_id: int, quiz_id: int, answers: dict, db: Session, current_user: Accounts):
    return submit_assessment_progress(
        request=request,
        module_id=module_id,
        assessment_id=quiz_id,
        answers=answers,
        db=db,
        current_user=current_user,
        assessment_type="quiz",
    )


def submit_assessment_progress(
    request: Request,
    module_id: int,
    assessment_id: int,
    answers: dict,
    db: Session,
    current_user: Accounts,
    assessment_type: str | None = None,
):
    _ensure_student(current_user)
    _ensure_enrolled_module(module_id, db, current_user)
    assessment_filters = [
        TeacherAssessment.id == assessment_id,
        TeacherAssessment.module_id == module_id,
    ]
    if assessment_type:
        assessment_filters.append(TeacherAssessment.assessment_type == assessment_type)

    assessment = db.query(TeacherAssessment).filter(*assessment_filters).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")

    if assessment.assessment_type == "quiz":
        topic_count = db.query(LearningTopic).filter(LearningTopic.module_id == module_id).count()
        completed_topic_count = db.query(StudentTopicProgress).filter(
            StudentTopicProgress.student_id == current_user.id,
            StudentTopicProgress.module_id == module_id,
            StudentTopicProgress.status == "completed",
        ).count()
        if topic_count and completed_topic_count < topic_count:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Complete all topics before taking the quiz")

    questions = assessment.questions or []
    total = len(questions)
    score = 0
    for index, question in enumerate(questions):
        expected = _normalize_answer(question.get("answer") or "")
        actual = _normalize_answer(str(answers.get(str(index), answers.get(index, ""))))
        if expected and expected == actual:
            score += 1

    progress = db.query(StudentQuizProgress).filter(
        StudentQuizProgress.student_id == current_user.id,
        StudentQuizProgress.assessment_id == assessment_id,
    ).first()
    if not progress:
        progress = StudentQuizProgress(
            student_id=current_user.id,
            module_id=module_id,
            assessment_id=assessment_id,
        )
        db.add(progress)

    progress.status = "completed"
    progress.score = score
    progress.total = total
    progress.answers = answers
    progress.completed_at = utc_now()
    db.commit()

    return {
        "score": score,
        "total": total,
        "progress": get_module_progress(request, module_id, db, current_user),
    }


def submit_class_activity_progress(request: Request, activity_id: int, answers: dict, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    activity = get_student_activity(request, activity_id, db, current_user)
    questions = activity.questions or []
    total = len(questions)
    score = 0
    for index, question in enumerate(questions):
        expected = _normalize_answer(question.get("answer") or "")
        actual = _normalize_answer(str(answers.get(str(index), answers.get(index, ""))))
        if expected and expected == actual:
            score += 1

    progress = db.query(StudentQuizProgress).filter(
        StudentQuizProgress.student_id == current_user.id,
        StudentQuizProgress.assessment_id == activity_id,
    ).first()
    if not progress:
        progress = StudentQuizProgress(
            student_id=current_user.id,
            module_id=None,
            assessment_id=activity_id,
        )
        db.add(progress)

    progress.status = "completed"
    progress.score = score
    progress.total = total
    progress.answers = answers
    progress.completed_at = utc_now()
    db.commit()

    return {
        "score": score,
        "total": total,
    }


def _get_student_profile(db: Session, current_user: Accounts):
    return db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()


def _ensure_enrolled_module(module_id: int, db: Session, current_user: Accounts):
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    grade_level = _grade_value(profile.grade_level)
    section = _normalize_section(profile.section)

    module = (
        db.query(TeacherModule.id)
        .join(TeacherClass, TeacherClass.id == TeacherModule.class_id)
        .filter(
            TeacherModule.id == module_id,
            TeacherModule.status == "Published",
            TeacherClass.grade_level == grade_level,
            func.lower(func.trim(TeacherClass.section)) == section.lower(),
        )
        .first()
    )
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")


def _normalize_answer(value: str):
    return " ".join(value.strip().lower().split())


def _grade_value(grade_level):
    return getattr(grade_level, "value", grade_level)


def _normalize_section(section: str):
    return " ".join(section.strip().split()).upper()


def _ensure_topics(db: Session, modules: list[TeacherModule]):
    changed = False
    for module in modules:
        if _needs_pdf_topic_regeneration(module):
            _replace_topic_records(db, module, _extract_pdf_logical_topics(Path(module.file_path), module.title, module.description))
            continue
        if module.topics:
            continue
        module.topics.append(LearningTopic(
            title="Introduction",
            description=module.description,
            content=f"{module.title}\n\n{module.description}\n\nUploaded file: {module.file_name or 'No file attached'}",
            sort_order=1,
        ))
        changed = True
    if changed:
        db.commit()
