from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session, joinedload

from models.learning_topic import LearningTopic
from models.module_checkpoint import ModuleCheckpoint
from models.remediation_activity import RemediationActivity
from models.remediation_intervention import RemediationIntervention
from models.remediation_target import RemediationTarget
from models.student_checkpoint_attempt import StudentCheckpointAttempt
from models.student_profile import StudentProfile
from models.teacher_module import TeacherModule
from schemas.remediation_schema import RemediationActivityCreate
from services.push_notification_service import send_push_to_accounts
from utils.enum import RoleEnum, StudentType
from utils.handsign.science_vocabulary import answers_match
from utils.utc_now import utc_now


QUESTION_VIDEO_DIR = Path("static/remediation_question_videos")
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi"}
MAX_VIDEO_BYTES = 100 * 1024 * 1024


def create_remediation_activity(payload: RemediationActivityCreate, db: Session, current_user) -> dict:
    module = _teacher_module(payload.module_id, db, current_user)
    activity = RemediationActivity(
        teacher_id=current_user.id,
        module_id=module.id,
        title=payload.title.strip(),
        description=payload.description.strip(),
        due_at=payload.due_at,
    )
    db.add(activity)
    db.flush()

    target_ids: set[int] = set()
    for item in payload.interventions:
        _validate_range(module, item.start_sort_order, item.end_sort_order)
        checkpoint = None
        if item.checkpoint_id is not None:
            checkpoint = db.query(ModuleCheckpoint).filter(
                ModuleCheckpoint.id == item.checkpoint_id,
                ModuleCheckpoint.module_id == module.id,
            ).first()
            if not checkpoint:
                raise HTTPException(status_code=422, detail="Selected checkpoint does not belong to this learning material.")
            if (checkpoint.start_sort_order, checkpoint.end_sort_order) != (item.start_sort_order, item.end_sort_order):
                raise HTTPException(status_code=422, detail="The selected checkpoint does not match the topic range.")

        _validate_hearing_impaired_targets(module, item.student_ids, db)
        questions = _stored_questions(item, checkpoint, db)
        intervention = RemediationIntervention(
            remediation_activity_id=activity.id,
            checkpoint_id=item.checkpoint_id,
            start_sort_order=item.start_sort_order,
            end_sort_order=item.end_sort_order,
            title=item.title.strip(),
            instructions=item.instructions.strip() if item.instructions else None,
            questions=questions,
        )
        db.add(intervention)
        db.flush()
        for student_id in item.student_ids:
            db.add(RemediationTarget(intervention_id=intervention.id, student_id=student_id))
            target_ids.add(student_id)

    db.commit()
    activity = _teacher_activity(activity.id, db, current_user)
    _notify_targets(activity, target_ids, db)
    return _teacher_activity_dict(activity, db)


def list_teacher_remediation_activities(db: Session, current_user) -> list[dict]:
    _ensure_teacher(current_user)
    activities = (
        db.query(RemediationActivity)
        .options(joinedload(RemediationActivity.interventions).joinedload(RemediationIntervention.targets))
        .filter(RemediationActivity.teacher_id == current_user.id)
        .order_by(RemediationActivity.created_at.desc())
        .all()
    )
    return [_teacher_activity_dict(activity, db) for activity in activities]


def upload_remediation_question_video(
    activity_id: int,
    intervention_id: int,
    question_index: int,
    video: UploadFile,
    db: Session,
    current_user,
) -> dict:
    activity = _teacher_activity(activity_id, db, current_user)
    intervention = next((item for item in activity.interventions if item.id == intervention_id), None)
    if not intervention:
        raise HTTPException(status_code=404, detail="Remediation topic group not found")

    questions = [dict(question) for question in intervention.questions or []]
    if question_index < 0 or question_index >= len(questions):
        raise HTTPException(status_code=404, detail="Support question not found")
    question = questions[question_index]
    if question.get("prompt_type") != "sign_video":
        raise HTTPException(status_code=422, detail="Only sign-language questions can receive a question video.")

    destination = _save_video(video, QUESTION_VIDEO_DIR, "Sign-language question videos")
    old_path = _question_video_path(question.get("sign_video_url"))
    question["sign_video_url"] = f"/static/remediation_question_videos/{destination.name}"
    questions[question_index] = question
    intervention.questions = questions
    db.commit()
    if old_path:
        old_path.unlink(missing_ok=True)
    return _teacher_activity_dict(_teacher_activity(activity.id, db, current_user), db)


def list_student_remediation_activities(db: Session, current_user) -> list[dict]:
    _ensure_student(current_user)
    targets = (
        db.query(RemediationTarget)
        .options(joinedload(RemediationTarget.intervention).joinedload(RemediationIntervention.activity))
        .filter(RemediationTarget.student_id == current_user.id)
        .order_by(RemediationTarget.created_at.desc())
        .all()
    )
    return [_student_target_dict(target, db) for target in targets]


def get_student_remediation_target(target_id: int, db: Session, current_user) -> dict:
    _ensure_student(current_user)
    target = (
        db.query(RemediationTarget)
        .options(joinedload(RemediationTarget.intervention).joinedload(RemediationIntervention.activity))
        .filter(RemediationTarget.id == target_id, RemediationTarget.student_id == current_user.id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Support activity not found")
    return _student_target_dict(target, db, include_topics=True)


def submit_student_remediation_target(target_id: int, answers: dict, db: Session, current_user) -> dict:
    _ensure_student(current_user)
    target = (
        db.query(RemediationTarget)
        .options(joinedload(RemediationTarget.intervention).joinedload(RemediationIntervention.activity))
        .filter(RemediationTarget.id == target_id, RemediationTarget.student_id == current_user.id)
        .first()
    )
    if not target:
        raise HTTPException(status_code=404, detail="Support activity not found")
    if target.status == "completed":
        return _student_target_dict(target, db, include_topics=True)
    questions = target.intervention.questions or []
    target.answers = answers or {}
    target.total = len(questions)
    target.score = _score_questions(questions, target.answers)
    target.status = "completed"
    target.completed_at = utc_now()
    db.commit()
    return _student_target_dict(target, db, include_topics=True)


def _ensure_teacher(current_user) -> None:
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")


def _ensure_student(current_user) -> None:
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student only")


def _teacher_module(module_id: int, db: Session, current_user) -> TeacherModule:
    _ensure_teacher(current_user)
    module = db.query(TeacherModule).filter(
        TeacherModule.id == module_id,
        TeacherModule.teacher_id == current_user.id,
        TeacherModule.class_id.isnot(None),
    ).first()
    if not module:
        raise HTTPException(status_code=404, detail="Learning material not found")
    return module


def _teacher_activity(activity_id: int, db: Session, current_user) -> RemediationActivity:
    _ensure_teacher(current_user)
    activity = (
        db.query(RemediationActivity)
        .options(joinedload(RemediationActivity.interventions).joinedload(RemediationIntervention.targets))
        .filter(RemediationActivity.id == activity_id, RemediationActivity.teacher_id == current_user.id)
        .first()
    )
    if not activity:
        raise HTTPException(status_code=404, detail="Support activity not found")
    return activity


def _validate_range(module: TeacherModule, start: int, end: int) -> None:
    if end < start:
        raise HTTPException(status_code=422, detail="The topic range is invalid.")
    count = module.topics and len([topic for topic in module.topics if start <= topic.sort_order <= end])
    if not count or count != end - start + 1:
        raise HTTPException(status_code=422, detail="The selected topic range is not available in this learning material.")


def _validate_hearing_impaired_targets(module: TeacherModule, student_ids: list[int], db: Session) -> None:
    if module.teacher_class is None:
        raise HTTPException(status_code=422, detail="Learning material must be assigned to a class.")
    rows = db.query(StudentProfile).filter(
        StudentProfile.account_id.in_(student_ids),
        StudentProfile.student_type == StudentType.HI,
        StudentProfile.grade_level_id == module.teacher_class.grade_level_id,
        StudentProfile.section_id == module.teacher_class.section_id,
    ).all()
    if {row.account_id for row in rows} != set(student_ids):
        raise HTTPException(status_code=422, detail="Support activities can only target hearing-impaired students assigned to this class.")


def _teacher_activity_dict(activity: RemediationActivity, db: Session) -> dict:
    student_names = {
        row.account_id: row.name
        for row in db.query(StudentProfile).filter(
            StudentProfile.account_id.in_([target.student_id for item in activity.interventions for target in item.targets])
        ).all()
    }
    return {
        "id": activity.id,
        "module_id": activity.module_id,
        "title": activity.title,
        "description": activity.description,
        "due_at": activity.due_at,
        "created_at": activity.created_at,
        "interventions": [
            {
                "id": item.id,
                "checkpoint_id": item.checkpoint_id,
                "start_sort_order": item.start_sort_order,
                "end_sort_order": item.end_sort_order,
                "title": item.title,
                "instructions": item.instructions,
                "questions": item.questions or [],
                "targets": [
                    {
                        "id": target.id,
                        "student_id": target.student_id,
                        "student_name": student_names.get(target.student_id),
                        "status": target.status,
                        "score": target.score,
                        "total": target.total,
                        "completed_at": target.completed_at,
                    }
                    for target in item.targets
                ],
            }
            for item in sorted(activity.interventions, key=lambda row: row.id)
        ],
    }


def _student_target_dict(target: RemediationTarget, db: Session, *, include_topics: bool = False) -> dict:
    intervention = target.intervention
    activity = intervention.activity
    questions = []
    for question in intervention.questions or []:
        student_question = {key: value for key, value in question.items() if key not in {"answer", "source_question_index"}}
        if student_question.get("prompt_type") == "sign_video":
            # The original text is retained for teacher reporting only; students receive the signed prompt.
            student_question.pop("prompt", None)
        questions.append(student_question)
    payload = {
        "id": target.id,
        "activity_id": activity.id,
        "module_id": activity.module_id,
        "activity_title": activity.title,
        "activity_description": activity.description,
        "due_at": activity.due_at,
        "title": intervention.title,
        "instructions": intervention.instructions,
        "start_sort_order": intervention.start_sort_order,
        "end_sort_order": intervention.end_sort_order,
        "questions": questions,
        "status": target.status,
        "score": target.score,
        "total": target.total,
        "completed_at": target.completed_at,
        "is_late": bool(activity.due_at and utc_now() > activity.due_at),
    }
    if include_topics:
        payload["topics"] = [
            {
                "id": topic.id,
                "title": topic.title,
                "description": topic.description,
                "content": topic.content,
                "image_url": topic.image_url,
                "page_image_urls": topic.page_image_urls or [],
                "sort_order": topic.sort_order,
            }
            for topic in db.query(LearningTopic).filter(
                LearningTopic.module_id == activity.module_id,
                LearningTopic.sort_order >= intervention.start_sort_order,
                LearningTopic.sort_order <= intervention.end_sort_order,
            ).order_by(LearningTopic.sort_order.asc()).all()
        ]
    return payload


def _score_questions(questions: list[dict], answers: dict) -> int:
    return sum(
        1
        for index, question in enumerate(questions)
        if question.get("answer") and answers_match(str(answers.get(str(index), answers.get(index, ""))), question["answer"])
    )


def _stored_questions(item, checkpoint: ModuleCheckpoint | None, db: Session) -> list[dict]:
    """Snapshot source questions for a support activity without exposing their text to students."""
    stored: list[dict] = []
    source_questions = checkpoint.questions or [] if checkpoint else []
    attempts = []
    if checkpoint:
        attempts = db.query(StudentCheckpointAttempt).filter(
            StudentCheckpointAttempt.checkpoint_id == checkpoint.id,
            StudentCheckpointAttempt.student_id.in_(item.student_ids),
        ).all()

    for question in item.questions:
        data = question.model_dump()
        if data.get("prompt_type") != "sign_video":
            stored.append(data)
            continue

        source_index = data.get("source_question_index")
        if checkpoint is None or source_index is None or source_index >= len(source_questions):
            raise HTTPException(status_code=422, detail="A sign-language question must reference a question in the selected checkpoint.")
        source = source_questions[source_index]
        source_answer = str(source.get("answer") or "").strip()
        if not source_answer:
            raise HTTPException(status_code=422, detail="The selected checkpoint question has no correct answer.")
        if not any(
            not answers_match(str((attempt.answers or {}).get(str(source_index), (attempt.answers or {}).get(source_index, ""))), source_answer)
            for attempt in attempts
        ):
            raise HTTPException(status_code=422, detail="Select at least one student who missed each sign-language source question.")

        data["prompt"] = str(source.get("prompt") or "").strip()
        correct_answer = _answer_text(source_answer)
        if data.get("question_type") == "multiple_choice":
            choices = [str(choice).strip() for choice in data.get("options") or []]
            if correct_answer not in choices:
                raise HTTPException(status_code=422, detail="Multiple-choice options must include the selected question's correct answer.")
            data["answer"] = _multiple_choice_answer(choices, correct_answer)
        else:
            data["answer"] = correct_answer
        stored.append(data)
    return stored


def _answer_text(answer: str) -> str:
    """Return the human-readable answer from the application's stored MC encoding."""
    if "CORRECT:" not in answer or "|" not in answer:
        return answer
    parts = [part.strip() for part in answer.split("|")]
    correct_letter = next((part.split(":", 1)[1].strip().upper() for part in parts if part.startswith("CORRECT:") and ":" in part), "")
    return next((part.split(":", 1)[1].strip() for part in parts if part.split(":", 1)[0].strip().upper() == correct_letter and ":" in part), answer)


def _multiple_choice_answer(choices: list[str], correct_answer: str) -> str:
    encoded = [f"{chr(65 + index)}:{choice}" for index, choice in enumerate(choices)]
    correct_index = choices.index(correct_answer)
    encoded.append(f"CORRECT:{chr(65 + correct_index)}")
    return "|".join(encoded)


def _save_video(video: UploadFile, directory: Path, label: str) -> Path:
    extension = Path(video.filename or "video.webm").suffix.lower() or ".webm"
    if extension not in ALLOWED_VIDEO_EXTENSIONS or (video.content_type and not video.content_type.startswith("video/")):
        raise HTTPException(status_code=400, detail="Upload an MP4, WEBM, MOV, or AVI video.")
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / f"{uuid4().hex}{extension}"
    video.file.seek(0)
    total = 0
    try:
        with destination.open("wb") as buffer:
            while True:
                chunk = video.file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_VIDEO_BYTES:
                    raise HTTPException(status_code=413, detail=f"{label} can be up to 100 MB.")
                buffer.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        video.file.seek(0)
    return destination


def _notify_targets(activity: RemediationActivity, target_ids: set[int], db: Session) -> None:
    try:
        send_push_to_accounts(
            db,
            list(target_ids),
            title="New support activity",
            body=f"Your teacher assigned {activity.title}.",
            url="/student/activities",
        )
    except Exception:
        pass


def _question_video_path(url: str | None) -> Path | None:
    if not url or not url.startswith("/static/remediation_question_videos/"):
        return None
    return QUESTION_VIDEO_DIR / Path(url).name
