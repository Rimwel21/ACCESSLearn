from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from models.learning_topic import LearningTopic
from models.topic_sign_video import TopicSignVideo
from models.teacher_module import TeacherModule
from utils.enum import RoleEnum


FOCUS_AREAS = {
    "change_in_matter": "Change in Matter",
    "photosynthesis": "Plant Processes / Photosynthesis",
    "force_and_motion": "Force and Motion",
    "water_cycle": "Water Cycle",
}
VIDEO_DIR = Path("static/learning_sign_videos")
ALLOWED_EXTENSIONS = {".mp4", ".webm", ".mov", ".avi"}
MAX_VIDEO_BYTES = 100 * 1024 * 1024


def list_topic_sign_videos(module_id: int, topic_id: int, db: Session, current_user) -> list[TopicSignVideo]:
    topic = _teacher_topic(module_id, topic_id, db, current_user)
    return sorted(topic.sign_videos, key=lambda item: item.id)


def upload_topic_sign_video(
    module_id: int,
    topic_id: int,
    focus_area: str,
    title: str | None,
    video: UploadFile,
    db: Session,
    current_user,
) -> TopicSignVideo:
    topic = _teacher_topic(module_id, topic_id, db, current_user)
    if focus_area not in FOCUS_AREAS:
        raise HTTPException(status_code=422, detail="Choose one of the four supported sign-language focus areas.")

    destination = _save_video(video)
    assignment = next((item for item in topic.sign_videos if item.focus_area == focus_area), None)
    old_path = _video_path(assignment.video_url) if assignment else None
    if assignment is None:
        assignment = TopicSignVideo(
            learning_topic_id=topic.id,
            focus_area=focus_area,
            title=(title or FOCUS_AREAS[focus_area]).strip()[:160],
            video_url=f"/static/learning_sign_videos/{destination.name}",
        )
        db.add(assignment)
    else:
        assignment.title = (title or FOCUS_AREAS[focus_area]).strip()[:160]
        assignment.video_url = f"/static/learning_sign_videos/{destination.name}"
    db.commit()
    db.refresh(assignment)
    if old_path:
        old_path.unlink(missing_ok=True)
    return assignment


def delete_topic_sign_video(module_id: int, topic_id: int, sign_video_id: int, db: Session, current_user) -> None:
    topic = _teacher_topic(module_id, topic_id, db, current_user)
    assignment = next((item for item in topic.sign_videos if item.id == sign_video_id), None)
    if not assignment:
        raise HTTPException(status_code=404, detail="Sign-language video assignment not found.")
    path = _video_path(assignment.video_url)
    db.delete(assignment)
    db.commit()
    if path:
        path.unlink(missing_ok=True)


def _teacher_topic(module_id: int, topic_id: int, db: Session, current_user) -> LearningTopic:
    if current_user.role != RoleEnum.teacher:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teacher only")
    topic = (
        db.query(LearningTopic)
        .join(TeacherModule, TeacherModule.id == LearningTopic.module_id)
        .filter(
            LearningTopic.id == topic_id,
            LearningTopic.module_id == module_id,
            TeacherModule.teacher_id == current_user.id,
        )
        .first()
    )
    if not topic:
        raise HTTPException(status_code=404, detail="Learning topic not found.")
    return topic


def _save_video(video: UploadFile) -> Path:
    extension = Path(video.filename or "sign-support.webm").suffix.lower() or ".webm"
    if extension not in ALLOWED_EXTENSIONS or (video.content_type and not video.content_type.startswith("video/")):
        raise HTTPException(status_code=400, detail="Upload an MP4, WEBM, MOV, or AVI video.")
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    destination = VIDEO_DIR / f"{uuid4().hex}{extension}"
    total = 0
    video.file.seek(0)
    try:
        with destination.open("wb") as buffer:
            while True:
                chunk = video.file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_VIDEO_BYTES:
                    raise HTTPException(status_code=413, detail="Sign-language videos can be up to 100 MB.")
                buffer.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    finally:
        video.file.seek(0)
    return destination


def _video_path(url: str | None) -> Path | None:
    if not url or not url.startswith("/static/learning_sign_videos/"):
        return None
    return VIDEO_DIR / Path(url).name
