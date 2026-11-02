from fastapi import HTTPException, Request, status
import re
from datetime import timedelta
from sqlalchemy.orm import Session, joinedload
from models.accounts import Accounts
from models.assessment_retake_request import AssessmentRetakeRequest
from models.learning_topic import LearningTopic
from models.student_profile import StudentProfile
from models.student_quiz_progress import StudentQuizProgress
from models.teacher_assessment import TeacherAssessment
from models.teacher_class import TeacherClass
from models.teacher_module import TeacherModule
from models.teacher_activity_week import TeacherActivityWeek
from schemas.teacher_assessment_schema import TeacherAssessmentCreate, TeacherAssessmentUpdate
from services.push_notification_service import queue_assessment_notification
from services.handsign.dataset_admin_service import week_labels
from utils.handsign.science_vocabulary import canonical_word
from utils.enum import RoleEnum
from utils.utc_now import utc_now


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


def get_activity_progress(request: Request, assessment_id: int, db: Session, current_user: Accounts):
    """Return one complete class roster joined to the activity's saved progress."""
    _ensure_teacher(current_user)
    assessment = db.query(TeacherAssessment).filter(
        TeacherAssessment.id == assessment_id,
        TeacherAssessment.teacher_id == current_user.id,
        TeacherAssessment.assessment_type == "activity",
    ).first()
    if not assessment or assessment.class_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")

    teacher_class = db.query(TeacherClass).options(
        joinedload(TeacherClass.grade_levels),
        joinedload(TeacherClass.sections),
    ).filter(
        TeacherClass.id == assessment.class_id,
        TeacherClass.teacher_id == current_user.id,
    ).first()
    if not teacher_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    students = db.query(StudentProfile).join(Accounts, Accounts.id == StudentProfile.account_id).filter(
        StudentProfile.grade_level_id == teacher_class.grade_level_id,
        StudentProfile.section_id == teacher_class.section_id,
        Accounts.role == RoleEnum.student,
    ).order_by(StudentProfile.name.asc()).all()
    student_ids = [student.account_id for student in students]
    progress_rows = db.query(StudentQuizProgress).filter(
        StudentQuizProgress.assessment_id == assessment.id,
        StudentQuizProgress.student_id.in_(student_ids),
    ).all() if student_ids else []
    progress_by_student = {progress.student_id: progress for progress in progress_rows}

    now = utc_now()
    total_questions = len(assessment.questions or [])
    rows = []
    summary = {
        "total_students": len(students),
        "not_started": 0,
        "in_progress": 0,
        "draft_complete": 0,
        "submitted": 0,
        "missing": 0,
        "late": 0,
        "graded": 0,
    }
    for student in students:
        progress = progress_by_student.get(student.account_id)
        answers = _valid_activity_answers(assessment, progress.answers if progress else {})
        answered_count = len(answers)
        submitted = bool(progress and progress.status == "completed")
        late = bool(submitted and assessment.due_at and _datetime_after(progress.completed_at, assessment.due_at))
        deadline_passed = bool(assessment.due_at and _datetime_after(now, assessment.due_at))

        if submitted:
            row_status = "late" if late else "submitted"
            summary["submitted"] += 1
            if late:
                summary["late"] += 1
        elif progress and progress.status == "missing":
            row_status = "missing"
            summary["missing"] += 1
        elif deadline_passed:
            row_status = "missing"
            summary["missing"] += 1
        elif not progress:
            row_status = "not_started"
            summary["not_started"] += 1
        elif total_questions and answered_count == total_questions:
            row_status = "draft_complete"
            summary["draft_complete"] += 1
        else:
            row_status = "in_progress"
            summary["in_progress"] += 1

        recently_active = bool(
            progress
            and not submitted
            and progress.updated_at
            and not _datetime_after(now - timedelta(minutes=5), progress.updated_at)
        )
        rows.append({
            "student_id": student.account_id,
            "student_name": student.name,
            "status": row_status,
            "answered_count": answered_count,
            "unanswered_count": max(total_questions - answered_count, 0),
            "total_questions": total_questions,
            "progress_percent": round(answered_count / total_questions * 100) if total_questions else 0,
            "last_saved_at": progress.updated_at if progress else None,
            "submitted": submitted,
            "submitted_at": progress.completed_at if submitted else None,
            "is_currently_working": recently_active,
            "answers": answers,
        })

    started = summary["total_students"] - summary["not_started"]
    summary["started"] = started
    summary["started_percent"] = round(started / summary["total_students"] * 100) if summary["total_students"] else 0
    summary["submitted_percent"] = round(summary["submitted"] / summary["total_students"] * 100) if summary["total_students"] else 0
    return {
        "activity_id": assessment.id,
        "activity_title": assessment.title,
        "class_id": teacher_class.id,
        "class_name": teacher_class.class_name,
        "grade_level": teacher_class.grade_levels.name if teacher_class.grade_levels else None,
        "section": teacher_class.sections.name if teacher_class.sections else None,
        "due_at": assessment.due_at,
        "summary": summary,
        "students": rows,
    }


def _valid_activity_answers(assessment: TeacherAssessment, answers: dict | None) -> dict[str, str]:
    cleaned: dict[str, str] = {}
    for index in range(len(assessment.questions or [])):
        value = (answers or {}).get(str(index))
        if value is None:
            value = (answers or {}).get(index)
        if isinstance(value, str) and value.strip():
            cleaned[str(index)] = value.strip()
    return cleaned


def _datetime_after(left, right) -> bool:
    if left is None or right is None:
        return False
    if left.tzinfo is None and right.tzinfo is not None:
        right = right.replace(tzinfo=None)
    elif left.tzinfo is not None and right.tzinfo is None:
        left = left.replace(tzinfo=None)
    return left > right


def create_teacher_assessment(request: Request, assessment: TeacherAssessmentCreate, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)
    _validate_assessment_assignment(assessment, db, current_user)
    _validate_week(assessment.week)
    _validate_weekly_identification_answers(assessment.assessment_type, assessment.week, assessment.questions, db)
    time_limit_seconds = _validate_time_limit_seconds(
        assessment.assessment_type,
        assessment.time_limit_seconds,
        assessment.time_limit,
    )

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
        time_limit=None,
        time_limit_seconds=time_limit_seconds,
        attempts_allowed=assessment.attempts_allowed,
        shuffle_questions=str(assessment.shuffle_questions).lower(),
        show_answers_after_submission=str(assessment.show_answers_after_submission).lower(),
        allow_text_answers=str(assessment.allow_text_answers).lower(),
        questions=[question.model_dump() for question in assessment.questions],
        due_at=assessment.due_at,
    )

    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)
    queue_assessment_notification(new_assessment.id)

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

    next_week = update_data.get("week", assessment.week)
    next_questions = update.questions if update.questions is not None else assessment.questions
    _validate_weekly_identification_answers(assessment_type, next_week, next_questions, db)

    for key, value in update_data.items():
        if key in {"shuffle_questions", "show_answers_after_submission", "allow_text_answers"} and isinstance(value, bool):
            setattr(assessment, key, str(value).lower())
        elif key == "questions" and value is not None:
            setattr(assessment, key, [question.model_dump() for question in update.questions or []])
        elif key in {"time_limit", "time_limit_seconds"}:
            continue
        else:
            setattr(assessment, key, value.strip() if isinstance(value, str) else value)

    if assessment.assessment_type == "activity":
        assessment.time_limit = None
        assessment.time_limit_seconds = None
    else:
        incoming_seconds = update_data.get("time_limit_seconds", assessment.time_limit_seconds)
        incoming_text = update_data.get("time_limit", assessment.time_limit)
        assessment.time_limit_seconds = _validate_time_limit_seconds(
            assessment.assessment_type,
            incoming_seconds,
            incoming_text,
        )
        assessment.time_limit = None

    db.commit()
    db.refresh(assessment)
    return assessment


def delete_teacher_assessment(request: Request, assessment_id: int, db: Session, current_user: Accounts):
    assessment = get_teacher_assessment(request, assessment_id, db, current_user)
    db.delete(assessment)
    db.commit()
    return {"detail": "Assessment deleted successfully"}


def list_retake_requests(
    request: Request,
    db: Session,
    current_user: Accounts,
    status_filter: str | None = None,
    assessment_type: str | None = None,
):
    _ensure_teacher(current_user)
    query = (
        db.query(AssessmentRetakeRequest, TeacherAssessment, StudentProfile)
        .join(TeacherAssessment, TeacherAssessment.id == AssessmentRetakeRequest.assessment_id)
        .outerjoin(StudentProfile, StudentProfile.account_id == AssessmentRetakeRequest.student_id)
        .filter(AssessmentRetakeRequest.teacher_id == current_user.id)
        .order_by(AssessmentRetakeRequest.created_at.desc())
    )
    if status_filter and status_filter != "all":
        query = query.filter(AssessmentRetakeRequest.status == status_filter)
    if assessment_type in {"quiz", "activity"}:
        query = query.filter(TeacherAssessment.assessment_type == assessment_type)

    rows = query.all()
    return [
        {
            "id": retake.id,
            "assessment_id": retake.assessment_id,
            "assessment_title": assessment.title,
            "assessment_type": assessment.assessment_type,
            "student_id": retake.student_id,
            "student_name": student.name if student else f"Student #{retake.student_id}",
            "status": retake.status,
            "reason": retake.reason,
            "request_type": retake.request_type,
            "created_at": retake.created_at,
            "reviewed_at": retake.reviewed_at,
        }
        for retake, assessment, student in rows
    ]


def set_student_retake_access(
    request: Request,
    assessment_id: int,
    student_id: int,
    action: str,
    db: Session,
    current_user: Accounts,
):
    _ensure_teacher(current_user)
    if action not in {"approved", "rejected"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be approved or rejected")

    assessment = get_teacher_assessment(request, assessment_id, db, current_user)
    _ensure_student_in_assessment_class(student_id, assessment, db, current_user)
    retake = db.query(AssessmentRetakeRequest).filter(
        AssessmentRetakeRequest.student_id == student_id,
        AssessmentRetakeRequest.assessment_id == assessment.id,
        AssessmentRetakeRequest.teacher_id == current_user.id,
    ).order_by(AssessmentRetakeRequest.created_at.desc()).first()

    if not retake:
        retake = AssessmentRetakeRequest(
            student_id=student_id,
            assessment_id=assessment.id,
            teacher_id=current_user.id,
            request_type="teacher_decision",
            reason="Teacher-controlled retake access",
        )
        db.add(retake)

    retake.status = action
    retake.reviewed_by = current_user.id
    retake.reviewed_at = utc_now()

    reset_count = 0
    if action == "approved":
        progress = db.query(StudentQuizProgress).filter(
            StudentQuizProgress.student_id == student_id,
            StudentQuizProgress.assessment_id == assessment.id,
        ).first()
        reset_count = _reset_progress_for_retake(progress)

    db.commit()
    db.refresh(retake)
    return {"detail": f"Retake access {action}", "status": retake.status, "reset_count": reset_count}


def review_retake_request(request: Request, retake_id: int, action: str, db: Session, current_user: Accounts):
    _ensure_teacher(current_user)
    if action not in {"approved", "rejected"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Action must be approved or rejected")

    retake = db.query(AssessmentRetakeRequest).filter(
        AssessmentRetakeRequest.id == retake_id,
        AssessmentRetakeRequest.teacher_id == current_user.id,
    ).first()
    if not retake:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Retake request not found")
    if retake.status != "pending":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Retake request has already been reviewed")

    db.query(AssessmentRetakeRequest).filter(
        AssessmentRetakeRequest.id != retake.id,
        AssessmentRetakeRequest.student_id == retake.student_id,
        AssessmentRetakeRequest.assessment_id == retake.assessment_id,
        AssessmentRetakeRequest.status == action,
    ).update({"status": "superseded"}, synchronize_session=False)

    retake.status = action
    retake.reviewed_by = current_user.id
    retake.reviewed_at = utc_now()

    reset_count = 0
    if action == "approved":
        progress = db.query(StudentQuizProgress).filter(
            StudentQuizProgress.student_id == retake.student_id,
            StudentQuizProgress.assessment_id == retake.assessment_id,
        ).first()
        reset_count = _reset_progress_for_retake(progress)

    db.commit()
    return {"detail": f"Retake request {action}", "reset_count": reset_count}


def _reset_progress_for_retake(progress: StudentQuizProgress | None) -> int:
    if not progress:
        return 0

    history = list(progress.attempt_history or [])
    completed_at = progress.completed_at.isoformat() if progress.completed_at else None
    already_archived = bool(
        completed_at
        and any(item.get("completed_at") == completed_at for item in history)
    )
    if progress.status == "completed" and not already_archived:
        attempt_number = max(progress.attempt_count or 0, len(history) + 1)
        history.append({
            "attempt_number": attempt_number,
            "score": progress.score,
            "total": progress.total,
            "answers": progress.answers or {},
            "submission_type": progress.submission_type,
            "completed_at": completed_at,
        })
        progress.attempt_count = attempt_number
        progress.attempt_history = history

    progress.status = "in_progress"
    progress.score = None
    progress.total = None
    progress.answers = {}
    progress.started_at = None
    progress.completed_at = None
    progress.time_limit_seconds = None
    progress.expires_at = None
    progress.submission_type = None
    return 1


def _ensure_student_in_assessment_class(
    student_id: int,
    assessment: TeacherAssessment,
    db: Session,
    current_user: Accounts,
) -> None:
    class_id = assessment.class_id
    if class_id is None and assessment.module_id is not None:
        module = db.query(TeacherModule).filter(
            TeacherModule.id == assessment.module_id,
            TeacherModule.teacher_id == current_user.id,
        ).first()
        class_id = module.class_id if module else None

    teacher_class = db.query(TeacherClass).filter(
        TeacherClass.id == class_id,
        TeacherClass.teacher_id == current_user.id,
    ).first()
    if not teacher_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    student = db.query(StudentProfile.id).filter(
        StudentProfile.account_id == student_id,
        StudentProfile.grade_level_id == teacher_class.grade_level_id,
        StudentProfile.section_id == teacher_class.section_id,
    ).first()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found in this class")


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
    module = None
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
    return module


def _validate_week(week: str | None):
    if week is not None and not re.fullmatch(r"Week ([1-9]|[1-9][0-9]{1,2})", week):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Week must be between Week 1 and Week 999.",
        )


def list_teacher_activity_weeks(request: Request, db: Session, current_user: Accounts) -> list[str]:
    _ensure_teacher(current_user)
    defaults = [f"Week {number}" for number in range(1, 9)]
    saved = [
        row.week for row in db.query(TeacherActivityWeek)
        .filter(TeacherActivityWeek.teacher_id == current_user.id)
        .order_by(TeacherActivityWeek.week)
        .all()
    ]
    existing_assessment_weeks = [
        row.week for row in db.query(TeacherAssessment.week)
        .filter(
            TeacherAssessment.teacher_id == current_user.id,
            TeacherAssessment.assessment_type == "activity",
            TeacherAssessment.week.isnot(None),
        )
        .all()
        if row.week
    ]
    return sorted(set(defaults + saved + existing_assessment_weeks), key=lambda week: int(week.removeprefix("Week ")))


def add_teacher_activity_week(week: str, request: Request, db: Session, current_user: Accounts) -> dict[str, object]:
    _ensure_teacher(current_user)
    _validate_week(week)
    existing = db.query(TeacherActivityWeek).filter_by(teacher_id=current_user.id, week=week).first()
    if existing:
        return {"week": week, "created": False}
    db.add(TeacherActivityWeek(teacher_id=current_user.id, week=week))
    db.commit()
    return {"week": week, "created": True}


def _validate_weekly_identification_answers(assessment_type: str, week: str | None, questions, db: Session) -> None:
    """Activities may only use sign labels configured for their selected week."""
    if assessment_type != "activity" or not week:
        return

    allowed_labels = set(week_labels(week, db))
    for index, question in enumerate(questions, start=1):
        question_type = question.question_type if hasattr(question, "question_type") else question.get("question_type")
        answer = question.answer if hasattr(question, "answer") else question.get("answer")
        if question_type != "identification" or not answer:
            continue
        if canonical_word(answer) not in allowed_labels:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Question {index}: choose an identification answer from {week}'s Handsign labels.",
            )


def _validate_time_limit_seconds(assessment_type: str, seconds: int | None, text_value: str | None = None):
    if assessment_type == "activity":
        return None

    if seconds is not None:
        if not isinstance(seconds, int) or isinstance(seconds, bool) or seconds <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz time limit must be a positive whole number of seconds")
        return seconds

    if text_value is None or not text_value.strip():
        return None

    text = text_value.strip().lower()
    match = re.fullmatch(r"(\d+)\s+(second|seconds|minute|minutes|hour|hours)", text)
    if not match:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz time limit must use seconds, minutes, or hours")

    amount = int(match.group(1))
    if amount <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz time limit must be greater than zero")

    unit = match.group(2)
    if unit.startswith("hour"):
        return amount * 3600
    if unit.startswith("minute"):
        return amount * 60
    return amount


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

    if class_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select a target class")

    existing_class = db.query(TeacherClass.id).filter(
        TeacherClass.id == class_id,
        TeacherClass.teacher_id == current_user.id,
    ).first()
    if not existing_class:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    if module_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select a learning material for the quiz")

    module = _validate_module_topic(module_id, topic_id, db, current_user)
    if module.class_id != class_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Selected learning material does not belong to the target class")


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
        "time_limit": None,
        "time_limit_seconds": None,
        "attempts_allowed": assessment.attempts_allowed,
        "shuffle_questions": _string_to_bool(assessment.shuffle_questions),
        "show_answers_after_submission": _string_to_bool(assessment.show_answers_after_submission),
        "allow_text_answers": _string_to_bool(getattr(assessment, "allow_text_answers", "false")),
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
                "submission_type": progress.submission_type,
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
