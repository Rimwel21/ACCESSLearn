import shutil
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from core.handsign_config import HandSignSettings, get_handsign_settings
from models.accounts import Accounts
from models.handsign_tutorial_practice import HandsignTutorialPractice
from models.student_quiz_progress import StudentQuizProgress
from services.handsign.word_gesture_service import is_word_trained
from services.handsign.word_scoring_service import target_reference_paths
from services.student_module_service import get_student_activity
from utils.handsign.science_vocabulary import canonical_word
from utils.utc_now import utc_now

ALLOWED_TUTORIAL_VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov', '.avi'}
ALLOWED_TUTORIAL_VIDEO_TYPES = {
    'video/mp4',
    'video/webm',
    'video/quicktime',
    'video/x-msvideo',
    'application/octet-stream',
}
TUTORIAL_VIDEO_FILENAMES = ('demo.mp4', 'demo.webm', 'demo.mov', 'demo.avi')
MAX_TUTORIAL_VIDEO_BYTES = 100 * 1024 * 1024


def _settings(settings: HandSignSettings | None = None) -> HandSignSettings:
    return settings or get_handsign_settings()


def tutorial_video_path(word: str, settings: HandSignSettings | None = None):
    config = _settings(settings)
    word_dir = config.resolved_tutorial_assets_path() / canonical_word(word)
    for name in TUTORIAL_VIDEO_FILENAMES:
        path = word_dir / name
        if path.exists():
            return path
    return None


async def save_tutorial_video(word: str, video: UploadFile, settings: HandSignSettings | None = None) -> dict:
    config = _settings(settings)
    target_word = canonical_word(word)
    if not target_word:
        raise ValueError("A tutorial answer word is required.")

    filename = Path(video.filename or "tutorial.webm").name
    extension = Path(filename).suffix.lower() or ".webm"
    if extension not in ALLOWED_TUTORIAL_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported tutorial video type. Upload MP4, WEBM, MOV, or AVI videos only.",
        )
    if video.content_type and video.content_type not in ALLOWED_TUTORIAL_VIDEO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported tutorial video type. Upload MP4, WEBM, MOV, or AVI videos only.",
        )

    word_dir = config.resolved_tutorial_assets_path() / target_word
    word_dir.mkdir(parents=True, exist_ok=True)

    for existing_name in TUTORIAL_VIDEO_FILENAMES:
        existing_path = word_dir / existing_name
        if existing_path.exists():
            existing_path.unlink()

    destination = word_dir / f"demo{extension}"
    video.file.seek(0)
    total_bytes = 0
    with destination.open("wb") as buffer:
        while True:
            chunk = video.file.read(1024 * 1024)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > MAX_TUTORIAL_VIDEO_BYTES:
                buffer.close()
                destination.unlink(missing_ok=True)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Tutorial video is too large. Upload a video up to 100 MB only.",
                )
            buffer.write(chunk)
    video.file.seek(0)
    return tutorial_status(target_word, config)
def tutorial_landmark_sample_path(word: str, settings: HandSignSettings | None = None):
    references = target_reference_paths(word, _settings(settings))
    return references[0] if references else None


def tutorial_status(word: str, settings: HandSignSettings | None = None) -> dict:
    config = _settings(settings)
    target_word = canonical_word(word)
    video = tutorial_video_path(target_word, config)
    sample = tutorial_landmark_sample_path(target_word, config)
    references = target_reference_paths(target_word, config)
    has_practice_dataset = len(references) > 0
    is_trained = is_word_trained(target_word, config)
    video_url = None
    if video:
        video_url = f"/static/handsign/tutorial_assets/{target_word}/{video.name}"
    return {
        "word": target_word,
        "has_video": video is not None,
        "video_path": str(video) if video else None,
        "video_url": video_url,
        "has_landmark_sample": sample is not None,
        "landmark_sample_path": str(sample) if sample else None,
        "has_practice_dataset": has_practice_dataset,
        "is_trained_in_word_model": is_trained,
        "reference_count": len(references),
        "can_practice": has_practice_dataset and is_trained,
    }


def save_practice_result(
    *,
    activity_id: int,
    word: str,
    attempt_scores: list[float],
    db: Session,
    current_user: Accounts,
) -> HandsignTutorialPractice:
    config = get_handsign_settings()
    if len(attempt_scores) != config.tutorial_attempt_count:
        raise ValueError(f"Exactly {config.tutorial_attempt_count} attempts are required.")

    activity = get_student_activity(request=None, activity_id=activity_id, db=db, current_user=current_user)
    progress = db.query(StudentQuizProgress).filter(
        StudentQuizProgress.student_id == current_user.id,
        StudentQuizProgress.assessment_id == activity_id,
    ).first()
    if not progress or progress.status != "completed":
        raise ValueError("Submit the activity answer before saving tutorial practice results.")

    target_word = canonical_word(word)
    expected_words = {
        canonical_word(question.get("answer"))
        for question in (activity.get("questions") or [])
        if question.get("answer")
    }
    if expected_words and target_word not in expected_words:
        raise ValueError(f"{target_word} is not an expected answer for this activity.")
    rounded_scores = [round(float(score), 2) for score in attempt_scores]
    highest_score = round(float(max(rounded_scores)), 2)

    record = db.query(HandsignTutorialPractice).filter(
        HandsignTutorialPractice.student_id == current_user.id,
        HandsignTutorialPractice.activity_id == activity_id,
        HandsignTutorialPractice.canonical_word == target_word,
    ).first()
    if not record:
        record = HandsignTutorialPractice(
            student_id=current_user.id,
            activity_id=activity_id,
            progress_id=progress.id if progress else None,
            canonical_word=target_word,
        )
        db.add(record)

    record.progress_id = progress.id if progress else record.progress_id
    record.attempt_scores = rounded_scores
    record.highest_score = highest_score
    record.completed_at = utc_now()
    record.updated_at = utc_now()
    db.commit()
    db.refresh(record)
    return record
