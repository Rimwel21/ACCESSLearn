from datetime import timedelta
from pathlib import Path
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload
from models.accounts import Accounts
from models.learning_topic import LearningTopic
from models.student_quiz_progress import StudentQuizProgress
from models.student_progress import StudentTopicProgress
from models.student_profile import StudentProfile
from models.teacher_assessment import TeacherAssessment
from models.teacher_class import TeacherClass
from models.teacher_module import TeacherModule
from services.teacher_module_service import _needs_material_topic_regeneration, _process_material_topics
from utils.enum import RoleEnum
from utils.handsign.science_vocabulary import answers_match
from utils.utc_now import utc_now


def _ensure_student(current_user: Accounts):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student only")


def list_student_modules(request: Request, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        return []

    modules = (
        db.query(TeacherModule)
        .join(TeacherClass, TeacherClass.id == TeacherModule.class_id)
        .options(joinedload(TeacherModule.topics), joinedload(TeacherModule.assessments))
        .filter(
            TeacherModule.status == "Published",
            TeacherClass.grade_level_id == profile.grade_level_id,
            TeacherClass.section_id == profile.section_id,
        )
        .order_by(TeacherModule.created_at.asc())
        .all()
    )
    _ensure_topics(db, modules)
    return modules


def list_upcoming_deadlines(request: Request, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        return []
    now = utc_now()

    modules = (
        db.query(TeacherModule)
        .join(TeacherClass, TeacherClass.id == TeacherModule.class_id)
        .filter(
            TeacherModule.status == "Published",
            TeacherModule.due_at.isnot(None),
            TeacherModule.due_at >= now,
            TeacherClass.grade_level_id == profile.grade_level_id,
            TeacherClass.section_id == profile.section_id,
        )
        .all()
    )
    class_activities = (
        db.query(TeacherAssessment)
        .join(TeacherClass, TeacherClass.id == TeacherAssessment.class_id)
        .filter(
            TeacherAssessment.assessment_type == "activity",
            TeacherAssessment.class_id.isnot(None),
            TeacherAssessment.due_at.isnot(None),
            TeacherAssessment.due_at >= now,
            TeacherClass.grade_level_id == profile.grade_level_id,
            TeacherClass.section_id == profile.section_id,
        )
        .all()
    )
    module_quizzes = (
        db.query(TeacherAssessment)
        .join(TeacherModule, TeacherModule.id == TeacherAssessment.module_id)
        .join(TeacherClass, TeacherClass.id == TeacherModule.class_id)
        .filter(
            TeacherAssessment.assessment_type == "quiz",
            TeacherAssessment.due_at.isnot(None),
            TeacherAssessment.due_at >= now,
            TeacherModule.status == "Published",
            TeacherClass.grade_level_id == profile.grade_level_id,
            TeacherClass.section_id == profile.section_id,
        )
        .all()
    )

    completed_assessment_ids = {
        row.assessment_id for row in db.query(StudentQuizProgress.assessment_id)
        .filter(
            StudentQuizProgress.student_id == current_user.id,
            StudentQuizProgress.status == "completed",
        )
        .all()
    }

    deadlines = []
    for module in modules:
        if _is_module_complete(request, module.id, db, current_user):
            continue
        deadlines.append({
            "id": f"module-{module.id}",
            "title": module.title,
            "item_type": "Learning Material",
            "due_at": module.due_at,
            "module_id": module.id,
            "assessment_id": None,
        })

    for assessment in module_quizzes + class_activities:
        if assessment.id in completed_assessment_ids:
            continue
        deadlines.append({
            "id": f"{assessment.assessment_type}-{assessment.id}",
            "title": assessment.title,
            "item_type": "Quiz" if assessment.assessment_type == "quiz" else "Activity",
            "due_at": assessment.due_at,
            "module_id": assessment.module_id,
            "assessment_id": assessment.id,
        })

    deadlines.sort(key=lambda item: item["due_at"])
    return deadlines


def list_student_activities(request: Request, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        return []

    activities = (
        db.query(TeacherAssessment)
        .join(TeacherClass, TeacherClass.id == TeacherAssessment.class_id)
        .filter(
            TeacherAssessment.assessment_type == "activity",
            TeacherAssessment.class_id.isnot(None),
            TeacherClass.grade_level_id == profile.grade_level_id,
            TeacherClass.section_id == profile.section_id,
        )
        .order_by(TeacherAssessment.created_at.asc())
        .all()
    )
    return [_assessment_to_dict(activity, db, current_user) for activity in activities]


def get_student_activity(request: Request, activity_id: int, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    activity = (
        db.query(TeacherAssessment)
        .join(TeacherClass, TeacherClass.id == TeacherAssessment.class_id)
        .filter(
            TeacherAssessment.id == activity_id,
            TeacherAssessment.assessment_type == "activity",
            TeacherAssessment.class_id.isnot(None),
            TeacherClass.grade_level_id == profile.grade_level_id,
            TeacherClass.section_id == profile.section_id,
        )
        .first()
    )
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    return _assessment_to_dict(activity, db, current_user)


def get_student_module(request: Request, module_id: int, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    module = (
        db.query(TeacherModule)
        .join(TeacherClass, TeacherClass.id == TeacherModule.class_id)
        .options(joinedload(TeacherModule.topics), joinedload(TeacherModule.assessments))
        .filter(
            TeacherModule.id == module_id,
            TeacherModule.status == "Published",
            TeacherClass.grade_level_id == profile.grade_level_id,
            TeacherClass.section_id == profile.section_id,
        )
        .first()
    )
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")
    _ensure_topics(db, [module])
    module.topics.sort(key=lambda topic: topic.sort_order)
    return {
        "id": module.id,
        "teacher_id": module.teacher_id,
        "class_id": module.class_id,
        "title": module.title,
        "description": module.description,
        "content_type": module.content_type,
        "week": module.week,
        "file_name": module.file_name,
        "file_type": module.file_type,
        "file_size": module.file_size,
        "status": module.status,
        "behavior_required": module.behavior_required,
        "due_at": module.due_at,
        "created_at": module.created_at,
        "updated_at": module.updated_at,
        "topics": module.topics,
        "assessments": [_assessment_to_dict(assessment, db, current_user) for assessment in module.assessments],
    }


def get_module_progress(request: Request, module_id: int, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    _ensure_enrolled_module(module_id, db, current_user)
    topic_ids = [
        topic.id for topic in db.query(LearningTopic.id)
        .join(TeacherModule, TeacherModule.id == LearningTopic.module_id)
        .filter(TeacherModule.id == module_id, TeacherModule.status == "Published")
        .order_by(LearningTopic.sort_order.asc(), LearningTopic.id.asc())
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
    current_completed_topic_ids = sorted(set(completed_ids) & set(topic_ids))
    current_completed_quiz_ids = sorted(set(completed_quiz_ids) & set(quiz_ids))
    completed = len(current_completed_topic_ids)
    total = len(topic_ids)
    completed_quizzes = len(current_completed_quiz_ids)
    total_quizzes = len(quiz_ids)
    total_items = total + total_quizzes
    completed_items = completed + completed_quizzes
    return {
        "completed_topic_ids": current_completed_topic_ids,
        "completed_quiz_ids": current_completed_quiz_ids,
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
    _ensure_topic_unlocked(module_id, topic_id, db, current_user)

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
        if progress.status == "completed" and status_value != "completed":
            return get_module_progress(request, module_id, db, current_user)
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


def start_quiz_progress(request: Request, module_id: int, quiz_id: int, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    _ensure_enrolled_module(module_id, db, current_user)
    assessment = _get_student_assessment(module_id, quiz_id, db, "quiz")
    _ensure_quiz_unlocked(module_id, db, current_user)

    progress = _get_or_create_assessment_progress(current_user.id, module_id, quiz_id, db)
    if progress.status == "completed":
        return {
            "started_at": progress.started_at,
            "time_limit_seconds": progress.time_limit_seconds,
            "expires_at": progress.expires_at,
            "remaining_seconds": 0,
            "expired": False,
            "completed": True,
            "score": progress.score,
            "total": progress.total,
            "submission_type": progress.submission_type,
            "progress": get_module_progress(request, module_id, db, current_user),
        }

    if not progress.started_at:
        progress.started_at = utc_now()
    if progress.time_limit_seconds is None and assessment.time_limit_seconds:
        progress.time_limit_seconds = assessment.time_limit_seconds
    if progress.time_limit_seconds and not progress.expires_at:
        progress.expires_at = progress.started_at + timedelta(seconds=progress.time_limit_seconds)

    expired = _is_time_limit_expired(assessment, progress)
    if expired and progress.status != "completed":
        _complete_assessment_progress(progress, assessment, progress.answers or {}, "timed_out")

    db.commit()
    if progress.status == "completed":
        return {
            "started_at": progress.started_at,
            "time_limit_seconds": progress.time_limit_seconds,
            "expires_at": progress.expires_at,
            "remaining_seconds": 0,
            "expired": expired,
            "completed": True,
            "score": progress.score,
            "total": progress.total,
            "submission_type": progress.submission_type,
            "progress": get_module_progress(request, module_id, db, current_user),
        }

    return {
        "started_at": progress.started_at,
        "time_limit_seconds": progress.time_limit_seconds,
        "expires_at": progress.expires_at,
        "remaining_seconds": _remaining_seconds(progress),
        "expired": expired,
        "completed": False,
        "submission_type": progress.submission_type,
    }


def save_quiz_answers(request: Request, module_id: int, quiz_id: int, answers: dict, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    _ensure_enrolled_module(module_id, db, current_user)
    assessment = _get_student_assessment(module_id, quiz_id, db, "quiz")
    _ensure_quiz_unlocked(module_id, db, current_user)

    progress = _get_assessment_progress(current_user.id, quiz_id, db)
    _ensure_quiz_started(assessment, progress)
    if progress.status == "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Quiz already submitted")
    if _is_time_limit_expired(assessment, progress):
        _complete_assessment_progress(progress, assessment, progress.answers or {}, "timed_out")
        db.commit()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Quiz time limit has expired")

    progress.answers = answers or {}
    db.commit()
    return {"detail": "Answers saved"}


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
    assessment = _get_student_assessment(module_id, assessment_id, db, assessment_type)

    if assessment.assessment_type == "quiz":
        _ensure_quiz_unlocked(module_id, db, current_user)

    progress = _get_assessment_progress(current_user.id, assessment_id, db) if assessment.assessment_type == "quiz" else _get_or_create_assessment_progress(current_user.id, module_id, assessment_id, db)
    if assessment.assessment_type == "quiz":
        _ensure_quiz_started(assessment, progress)

    if progress.status == "completed":
        return {
            "score": progress.score or 0,
            "total": progress.total or 0,
            "submission_type": progress.submission_type,
            "progress": get_module_progress(request, module_id, db, current_user),
        }

    if assessment.assessment_type == "quiz" and _is_time_limit_expired(assessment, progress):
        _complete_assessment_progress(progress, assessment, progress.answers or {}, "timed_out")
    else:
        _complete_assessment_progress(progress, assessment, answers, "manual")
    db.commit()

    return {
        "score": progress.score or 0,
        "total": progress.total or 0,
        "submission_type": progress.submission_type,
        "progress": get_module_progress(request, module_id, db, current_user),
    }


def submit_class_activity_progress(request: Request, activity_id: int, answers: dict, db: Session, current_user: Accounts):
    _ensure_student(current_user)
    activity = get_student_activity(request, activity_id, db, current_user)
    progress = db.query(StudentQuizProgress).filter(
        StudentQuizProgress.student_id == current_user.id,
        StudentQuizProgress.assessment_id == activity_id,
    ).first()
    if progress and progress.status == "completed":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Activity already submitted")

    questions = activity.get("questions") or []
    total = len(questions)
    score = 0
    for index, question in enumerate(questions):
        expected = question.get("answer") or ""
        actual = str(answers.get(str(index), answers.get(index, "")))
        if expected and answers_match(actual, expected):
            score += 1

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
    progress.started_at = progress.started_at or utc_now()
    progress.submission_type = "manual"
    progress.completed_at = utc_now()
    db.commit()

    return {
        "score": score,
        "total": total,
    }


def _get_student_assessment(module_id: int, assessment_id: int, db: Session, assessment_type: str | None = None):
    assessment_filters = [
        TeacherAssessment.id == assessment_id,
        TeacherAssessment.module_id == module_id,
    ]
    if assessment_type:
        assessment_filters.append(TeacherAssessment.assessment_type == assessment_type)

    assessment = db.query(TeacherAssessment).filter(*assessment_filters).first()
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return assessment


def _ensure_quiz_unlocked(module_id: int, db: Session, current_user: Accounts):
    topic_count = db.query(LearningTopic).filter(LearningTopic.module_id == module_id).count()
    completed_topic_count = db.query(StudentTopicProgress).filter(
        StudentTopicProgress.student_id == current_user.id,
        StudentTopicProgress.module_id == module_id,
        StudentTopicProgress.status == "completed",
    ).count()
    if topic_count and completed_topic_count < topic_count:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Complete all topics before taking the quiz")


def _get_or_create_assessment_progress(student_id: int, module_id: int | None, assessment_id: int, db: Session):
    progress = db.query(StudentQuizProgress).filter(
        StudentQuizProgress.student_id == student_id,
        StudentQuizProgress.assessment_id == assessment_id,
    ).first()
    if not progress:
        progress = StudentQuizProgress(
            student_id=student_id,
            module_id=module_id,
            assessment_id=assessment_id,
        )
        db.add(progress)
    return progress


def _get_assessment_progress(student_id: int, assessment_id: int, db: Session):
    progress = db.query(StudentQuizProgress).filter(
        StudentQuizProgress.student_id == student_id,
        StudentQuizProgress.assessment_id == assessment_id,
    ).first()
    if not progress:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start the quiz before submitting answers")
    return progress


def _ensure_quiz_started(assessment: TeacherAssessment, progress: StudentQuizProgress):
    if assessment.assessment_type == "quiz" and not progress.started_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start the quiz before submitting answers")


def _complete_assessment_progress(progress: StudentQuizProgress, assessment: TeacherAssessment, answers: dict, submission_type: str):
    questions = assessment.questions or []
    score = _score_answers(questions, answers or {})

    progress.status = "completed"
    progress.score = score
    progress.total = len(questions)
    progress.answers = answers or {}
    progress.started_at = progress.started_at or utc_now()
    progress.submission_type = submission_type
    progress.completed_at = utc_now()


def _score_answers(questions: list[dict], answers: dict):
    score = 0
    for index, question in enumerate(questions):
        expected = question.get("answer") or ""
        actual = str(answers.get(str(index), answers.get(index, "")))
        if expected and answers_match(actual, expected):
            score += 1
    return score


def _is_time_limit_expired(assessment: TeacherAssessment, progress: StudentQuizProgress):
    if not progress.time_limit_seconds or not progress.started_at:
        return False
    expires_at = progress.expires_at or (progress.started_at + timedelta(seconds=progress.time_limit_seconds))
    return utc_now() >= expires_at


def _remaining_seconds(progress: StudentQuizProgress):
    if not progress.expires_at:
        return None
    return max(0, int((progress.expires_at - utc_now()).total_seconds()))


def _get_student_profile(db: Session, current_user: Accounts):
    return (
        db.query(StudentProfile)
        .options(
            joinedload(StudentProfile.grade_level),
            joinedload(StudentProfile.section)
        )
        .filter(StudentProfile.account_id == current_user.id)
        .first()
    )


def _ensure_enrolled_module(module_id: int, db: Session, current_user: Accounts):
    profile = _get_student_profile(db, current_user)
    if not profile or not profile.grade_level or not profile.section:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")

    module = (
        db.query(TeacherModule.id)
        .join(TeacherClass, TeacherClass.id == TeacherModule.class_id)
        .filter(
            TeacherModule.id == module_id,
            TeacherModule.status == "Published",
            TeacherClass.grade_level_id == profile.grade_level_id,
            TeacherClass.section_id == profile.section_id,
        )
        .first()
    )
    if not module:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Module not found")


def _ensure_topic_unlocked(module_id: int, topic_id: int, db: Session, current_user: Accounts):
    topic_ids = [
        row.id for row in db.query(LearningTopic.id)
        .filter(LearningTopic.module_id == module_id)
        .order_by(LearningTopic.sort_order.asc(), LearningTopic.id.asc())
        .all()
    ]
    try:
        topic_index = topic_ids.index(topic_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    if topic_index == 0:
        return

    previous_topic_id = topic_ids[topic_index - 1]
    previous_completed = db.query(StudentTopicProgress.id).filter(
        StudentTopicProgress.student_id == current_user.id,
        StudentTopicProgress.module_id == module_id,
        StudentTopicProgress.topic_id == previous_topic_id,
        StudentTopicProgress.status == "completed",
    ).first()
    if not previous_completed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete the previous topic before opening this topic",
        )


def _is_module_complete(request: Request, module_id: int, db: Session, current_user: Accounts):
    progress = get_module_progress(request, module_id, db, current_user)
    total_items = progress["total_topics"] + progress["total_quizzes"]
    completed_items = progress["completed_topics"] + progress["completed_quizzes"]
    return total_items > 0 and completed_items == total_items


def _normalize_answer(value: str):
    return " ".join(value.strip().lower().split())


def _assessment_to_dict(assessment: TeacherAssessment, db: Session | None = None, current_user: Accounts | None = None):
    progress = None
    if db is not None and current_user is not None:
        progress = db.query(StudentQuizProgress).filter(
            StudentQuizProgress.student_id == current_user.id,
            StudentQuizProgress.assessment_id == assessment.id,
        ).first()

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
        "time_limit": assessment.time_limit if assessment.assessment_type == "quiz" else None,
        "time_limit_seconds": assessment.time_limit_seconds if assessment.assessment_type == "quiz" else None,
        "attempts_allowed": assessment.attempts_allowed,
        "shuffle_questions": _string_to_bool(assessment.shuffle_questions),
        "show_answers_after_submission": _string_to_bool(assessment.show_answers_after_submission),
        "questions": assessment.questions or [],
        "due_at": assessment.due_at,
        "student_status": progress.status if progress else None,
        "student_score": progress.score if progress else None,
        "student_total": progress.total if progress else None,
        "student_completed_at": progress.completed_at if progress else None,
        "student_started_at": progress.started_at if progress else None,
        "student_expires_at": progress.expires_at if progress else None,
        "student_remaining_seconds": _remaining_seconds(progress) if progress and progress.status != "completed" else None,
        "student_submission_type": progress.submission_type if progress else None,
        "student_answers": progress.answers if progress else {},
        "created_at": assessment.created_at,
        "updated_at": assessment.updated_at,
    }


def _string_to_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _ensure_topics(db: Session, modules: list[TeacherModule]):
    changed = False
    for module in modules:
        if _needs_material_topic_regeneration(module):
            _process_material_topics(db, module, Path(module.file_path))
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
