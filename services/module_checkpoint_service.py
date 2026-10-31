from __future__ import annotations

from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from models.module_checkpoint import ModuleCheckpoint
from models.student_checkpoint_attempt import StudentCheckpointAttempt
from models.student_module_learning_summary import StudentModuleLearningSummary
from models.student_profile import StudentProfile
from models.student_progress import StudentTopicProgress
from models.learning_topic import LearningTopic
from models.teacher_module import TeacherModule
from schemas.teacher_module_schema import ModuleCheckpointCreate
from services.push_notification_service import send_push_to_accounts
from utils.enum import NotificationCategoryEnum, NotificationPriorityEnum, RoleEnum, StudentType
from utils.handsign.science_vocabulary import answers_match
from utils.utc_now import utc_now


def replace_module_checkpoints(
    request: Request,
    module_id: int,
    checkpoints: list[ModuleCheckpointCreate],
    db: Session,
    current_user,
):
    module = _teacher_module(module_id, db, current_user)
    topic_orders = {row.sort_order for row in module.topics}
    starts: set[int] = set()
    for item in checkpoints:
        if item.end_sort_order - item.start_sort_order != 9:
            raise HTTPException(status_code=422, detail="Each checkpoint must cover exactly 10 topics.")
        if item.start_sort_order in starts:
            raise HTTPException(status_code=422, detail="Checkpoint topic ranges cannot overlap.")
        starts.add(item.start_sort_order)
        expected_orders = set(range(item.start_sort_order, item.end_sort_order + 1))
        if not expected_orders.issubset(topic_orders):
            raise HTTPException(status_code=422, detail="A checkpoint range must match generated topics in this learning material.")

    db.query(ModuleCheckpoint).filter(ModuleCheckpoint.module_id == module.id).delete(synchronize_session=False)
    for item in sorted(checkpoints, key=lambda value: value.start_sort_order):
        db.add(ModuleCheckpoint(
            module_id=module.id,
            start_sort_order=item.start_sort_order,
            end_sort_order=item.end_sort_order,
            title=item.title.strip(),
            questions=[question.model_dump() for question in item.questions],
        ))
    db.commit()
    return teacher_module_checkpoints(module, db)


def teacher_module_checkpoints(module: TeacherModule, db: Session) -> list[dict]:
    return [_checkpoint_dict(checkpoint) for checkpoint in sorted(module.checkpoints, key=lambda row: row.start_sort_order)]


def student_module_checkpoints(module: TeacherModule, db: Session, current_user) -> list[dict]:
    attempts = {
        row.checkpoint_id: row
        for row in db.query(StudentCheckpointAttempt).join(ModuleCheckpoint).filter(
            StudentCheckpointAttempt.student_id == current_user.id,
            ModuleCheckpoint.module_id == module.id,
        ).all()
    }
    return [
        _checkpoint_dict(checkpoint, attempts.get(checkpoint.id), include_answers=False)
        for checkpoint in sorted(module.checkpoints, key=lambda row: row.start_sort_order)
    ]


def submit_checkpoint(
    request: Request,
    module_id: int,
    checkpoint_id: int,
    answers: dict,
    db: Session,
    current_user,
):
    _ensure_student(current_user)
    checkpoint = (
        db.query(ModuleCheckpoint)
        .join(TeacherModule)
        .filter(
            ModuleCheckpoint.id == checkpoint_id,
            ModuleCheckpoint.module_id == module_id,
            TeacherModule.status == "Published",
        )
        .first()
    )
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")

    _ensure_student_enrolled(checkpoint.module, db, current_user)
    _ensure_block_topics_completed(checkpoint, db, current_user)

    attempt = db.query(StudentCheckpointAttempt).filter_by(
        student_id=current_user.id,
        checkpoint_id=checkpoint.id,
    ).first()
    if attempt:
        return {
            "score": attempt.score,
            "total": attempt.total,
            "completed": True,
            "checkpoint": _checkpoint_dict(checkpoint, attempt, include_answers=False),
        }

    score = _score_questions(checkpoint.questions or [], answers)
    attempt = StudentCheckpointAttempt(
        student_id=current_user.id,
        checkpoint_id=checkpoint.id,
        answers=answers or {},
        score=score,
        total=len(checkpoint.questions or []),
        completed_at=utc_now(),
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    _notify_teacher_when_module_checkpoints_complete(checkpoint.module, db, current_user)
    return {
        "score": attempt.score,
        "total": attempt.total,
        "completed": True,
        "checkpoint": _checkpoint_dict(checkpoint, attempt, include_answers=False),
    }


def checkpoint_summary(request: Request, module_id: int, db: Session, current_user):
    module = _teacher_module(module_id, db, current_user)
    checkpoints = sorted(module.checkpoints, key=lambda row: row.start_sort_order)
    results = []
    for checkpoint in checkpoints:
        rows = (
            db.query(StudentCheckpointAttempt, StudentProfile)
            .join(StudentProfile, StudentProfile.account_id == StudentCheckpointAttempt.student_id)
            .filter(StudentCheckpointAttempt.checkpoint_id == checkpoint.id)
            .all()
        )
        attempts = [
            {
                "student_id": attempt.student_id,
                "student_name": student.name,
                "score": attempt.score,
                "total": attempt.total,
                "completed_at": attempt.completed_at,
                "missed_question_indexes": _missed_question_indexes(checkpoint.questions or [], attempt.answers or {}),
            }
            for attempt, student in rows
            if student.student_type == StudentType.HI
        ]
        for attempt in attempts:
            # A student who missed even one question is a useful suggested
            # target for question-specific support; a 4/5 score still matters.
            attempt["struggling"] = bool(attempt["missed_question_indexes"])
        results.append({
            **_checkpoint_dict(checkpoint),
            "attempts": attempts,
            "struggling_students": [item for item in attempts if item["struggling"]],
        })
    return {"module_id": module.id, "module_title": module.title, "checkpoints": results}


def _teacher_module(module_id: int, db: Session, current_user) -> TeacherModule:
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")
    module = db.query(TeacherModule).filter(
        TeacherModule.id == module_id,
        TeacherModule.teacher_id == current_user.id,
    ).first()
    if not module:
        raise HTTPException(status_code=404, detail="Learning material not found")
    return module


def _ensure_student(current_user):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student only")


def _ensure_student_enrolled(module: TeacherModule, db: Session, current_user) -> None:
    profile = db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()
    if not profile or module.class_id is None or module.teacher_class is None:
        raise HTTPException(status_code=404, detail="Learning material not found")
    teacher_class = module.teacher_class
    if profile.grade_level_id != teacher_class.grade_level_id or profile.section_id != teacher_class.section_id:
        raise HTTPException(status_code=404, detail="Learning material not found")


def _ensure_block_topics_completed(checkpoint: ModuleCheckpoint, db: Session, current_user) -> None:
    expected = set(range(checkpoint.start_sort_order, checkpoint.end_sort_order + 1))
    completed = {
        row.sort_order
        for row in db.query(LearningTopic)
        .join(StudentTopicProgress, StudentTopicProgress.topic_id == LearningTopic.id)
        .filter(
            StudentTopicProgress.student_id == current_user.id,
            StudentTopicProgress.module_id == checkpoint.module_id,
            StudentTopicProgress.status == "completed",
        )
        .all()
    }
    if not expected.issubset(completed):
        raise HTTPException(status_code=403, detail="Complete the 10 topics before submitting this checkpoint.")


def _score_questions(questions: list[dict], answers: dict) -> int:
    score = 0
    for index, question in enumerate(questions):
        expected = question.get("answer") or ""
        actual = str(answers.get(str(index), answers.get(index, "")))
        if expected and answers_match(actual, expected):
            score += 1
    return score


def _missed_question_indexes(questions: list[dict], answers: dict) -> list[int]:
    return [
        index
        for index, question in enumerate(questions)
        if question.get("answer") and not answers_match(str(answers.get(str(index), answers.get(index, ""))), question["answer"])
    ]


def _checkpoint_dict(checkpoint: ModuleCheckpoint, attempt: StudentCheckpointAttempt | None = None, *, include_answers: bool = True) -> dict:
    questions = []
    for question in checkpoint.questions or []:
        item = dict(question)
        if not include_answers:
            item.pop("answer", None)
        questions.append(item)
    return {
        "id": checkpoint.id,
        "module_id": checkpoint.module_id,
        "start_sort_order": checkpoint.start_sort_order,
        "end_sort_order": checkpoint.end_sort_order,
        "title": checkpoint.title,
        "questions": questions,
        "student_status": "completed" if attempt else None,
        "student_score": attempt.score if attempt else None,
        "student_total": attempt.total if attempt else None,
        "student_completed_at": attempt.completed_at if attempt else None,
    }


def _notify_teacher_when_module_checkpoints_complete(module: TeacherModule, db: Session, current_user) -> None:
    checkpoint_ids = [row.id for row in module.checkpoints]
    if not checkpoint_ids:
        return
    complete_count = db.query(StudentCheckpointAttempt.id).filter(
        StudentCheckpointAttempt.student_id == current_user.id,
        StudentCheckpointAttempt.checkpoint_id.in_(checkpoint_ids),
    ).count()
    if complete_count != len(checkpoint_ids):
        return

    summary = db.query(StudentModuleLearningSummary).filter_by(
        student_id=current_user.id,
        module_id=module.id,
    ).first()
    if summary and summary.teacher_notified_at:
        return
    if not summary:
        summary = StudentModuleLearningSummary(student_id=current_user.id, module_id=module.id)
        db.add(summary)
    summary.completed_at = utc_now()
    summary.teacher_notified_at = utc_now()
    db.commit()

    profile = db.query(StudentProfile).filter(StudentProfile.account_id == current_user.id).first()
    student_name = profile.name if profile else f"Student #{current_user.id}"
    try:
        from services.notification_service import create_notification
        create_notification(
            db,
            recipient_id=module.teacher_id,
            title="Learning material checkpoint report ready",
            description=f"{student_name} completed all checkpoint questions for {module.title}.",
            icon="📘",
            priority=NotificationPriorityEnum.medium,
            category=NotificationCategoryEnum.teacher,
            related_user_id=current_user.id,
            related_page=f"/teacher/modules/{module.id}/preview",
        )
        send_push_to_accounts(
            db,
            [module.teacher_id],
            title="Checkpoint report ready",
            body=f"{student_name} completed {module.title}.",
            url=f"/teacher/modules/{module.id}/preview",
        )
    except Exception:
        # Reporting must never invalidate an already submitted student checkpoint.
        pass
