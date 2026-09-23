import json
import logging
import shutil
import subprocess
import sys
import tempfile
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from sqlalchemy.orm import Session

from core.handsign_config import get_handsign_settings
from models.handsign_dataset_label import HandsignDatasetLabel
from models.handsign_dataset_week import HandsignDatasetWeek
from utils.handsign.image import decode_base64_image
from utils.handsign.science_vocabulary import SUPPORTED_SCIENCE_SIGNS, WEEKLY_SCIENCE_SIGN_LABELS, canonical_word
from utils.handsign.word_gesture_features import FEATURE_VERSION, FRAME_FEATURE_LENGTH, holistic_result_to_feature_vector, resample_sequence

SAMPLE_REQUIREMENT_OPTIONS = (5, 10, 20, 40)
DEFAULT_SAMPLES_REQUIRED = 40
MIN_TRAINING_LABELS = 2
TRAINING_TREE_COUNT = 250
_training_lock = threading.Lock()
_training_process: subprocess.Popen | None = None
_training_job_dir: Path | None = None
_training_status = {
    "status": "idle",
    "message": "No training job has started yet.",
    "started_at": None,
    "finished_at": None,
    "processed_samples": 0,
    "total_samples": 0,
    "eligible_labels": 0,
    "trained_trees": 0,
    "total_trees": TRAINING_TREE_COUNT,
}
logger = logging.getLogger(__name__)


def normalize_week(week: str | None) -> str:
    digits = "".join(character for character in str(week or "").upper() if character.isdigit())
    if digits not in {str(number) for number in range(1, 1000)}:
        raise ValueError("Choose a week from Week 1 through Week 999.")
    return f"WEEK{digits}"


def _seed_default_labels(db: Session) -> None:
    for number in range(1, 9):
        _ensure_week(db, f"WEEK{number}")
    for week, labels in WEEKLY_SCIENCE_SIGN_LABELS.items():
        if week not in {f"WEEK{number}" for number in range(1, 9)}:
            continue
        for label in labels:
            target = canonical_word(label)
            exists = db.query(HandsignDatasetLabel.id).filter_by(week=week, label=target).first()
            if not exists:
                db.add(HandsignDatasetLabel(week=week, label=target))
    db.commit()


def _ensure_week(db: Session, week: str) -> None:
    if not db.query(HandsignDatasetWeek.id).filter_by(key=week).first():
        db.add(HandsignDatasetWeek(key=week))


def available_weeks(db: Session) -> list[str]:
    _seed_default_labels(db)
    weeks = [row.key for row in db.query(HandsignDatasetWeek).all()]
    return sorted(weeks, key=lambda week: int(week.removeprefix("WEEK")))


def add_dataset_week(week: str, db: Session) -> dict[str, str | bool]:
    target = normalize_week(week)
    _seed_default_labels(db)
    existing = db.query(HandsignDatasetWeek.id).filter_by(key=target).first()
    if existing:
        return {"week": target, "created": False}
    db.add(HandsignDatasetWeek(key=target))
    db.commit()
    return {"week": target, "created": True}


def weekly_label_catalog(db: Session) -> dict[str, list[str]]:
    _seed_default_labels(db)
    catalog = {week: [] for week in available_weeks(db)}
    for item in db.query(HandsignDatasetLabel).order_by(HandsignDatasetLabel.week, HandsignDatasetLabel.label).all():
        catalog.setdefault(item.week, []).append(item.label)
    return catalog


def add_dataset_label(label: str, week: str, db: Session) -> dict[str, str | bool]:
    target = canonical_word(label)
    if not target:
        raise ValueError("Enter a valid label.")
    group = normalize_week(week)
    _seed_default_labels(db)
    _ensure_week(db, group)
    existing = db.query(HandsignDatasetLabel).filter_by(week=group, label=target).first()
    if existing:
        return {"label": target, "week": group, "created": False}
    db.add(HandsignDatasetLabel(week=group, label=target))
    db.commit()
    return {"label": target, "week": group, "created": True}


def _label_requirements(db: Session) -> dict[str, int]:
    requirements: dict[str, int] = {}
    for item in db.query(HandsignDatasetLabel).all():
        requirement = int(item.samples_required or DEFAULT_SAMPLES_REQUIRED)
        if requirement not in SAMPLE_REQUIREMENT_OPTIONS:
            requirement = DEFAULT_SAMPLES_REQUIRED
        label = canonical_word(item.label)
        requirements[label] = min(requirements.get(label, requirement), requirement)
    return requirements


def _sample_count_for_label(group: str, label: str) -> int:
    config = get_handsign_settings()
    directory = config.resolved_word_gesture_dataset_path() / group / label
    return len(list(directory.glob("*.npz"))) if directory.exists() else 0


def set_dataset_label_samples_required(label: str, week: str, samples_required: int, db: Session) -> dict[str, object]:
    if samples_required not in SAMPLE_REQUIREMENT_OPTIONS:
        raise ValueError("Choose 5, 10, 20, or 40 samples.")

    group, target = _group_and_label(label, week, db)
    item = db.query(HandsignDatasetLabel).filter_by(week=group, label=target).first()
    if item is None:
        raise ValueError("That label is not assigned to the selected week.")

    item.samples_required = samples_required
    db.commit()
    sample_count = _sample_count_for_label(group, target)
    return {
        "label": target,
        "week": group,
        "samples_required": samples_required,
        "sample_count": sample_count,
        "ready_to_train": sample_count >= samples_required,
    }


def week_labels(week: str, db: Session) -> list[str]:
    return weekly_label_catalog(db).get(normalize_week(week), [])


def week_label_requirements(week: str, db: Session) -> dict[str, int]:
    group = normalize_week(week)
    return {
        item.label: int(item.samples_required or DEFAULT_SAMPLES_REQUIRED)
        for item in db.query(HandsignDatasetLabel).filter_by(week=group).all()
    }


def _group_and_label(label: str, week: str | None, db: Session):
    target = canonical_word(label)
    group = normalize_week(week)
    if target not in week_labels(group, db):
        raise ValueError("That label is not assigned to the selected week.")
    return group, target


def admin_dataset_summary(db: Session):
    from services.handsign.word_gesture_service import word_gesture_summary
    _refresh_training_status()
    word_summary = word_gesture_summary()
    requirements = _label_requirements(db)
    complete_labels = [
        item["label"] for item in word_summary["classes"]
        if item["sample_count"] >= requirements.get(item["label"], DEFAULT_SAMPLES_REQUIRED)
    ]
    incomplete_labels = [
        {"label": item["label"], "sample_count": item["sample_count"]}
        for item in word_summary["classes"]
        if item["sample_count"] < requirements.get(item["label"], DEFAULT_SAMPLES_REQUIRED)
    ]
    return {
        **word_summary,
        "samples_required": DEFAULT_SAMPLES_REQUIRED,
        "sample_requirement_options": list(SAMPLE_REQUIREMENT_OPTIONS),
        "label_requirements": [
            {"week": item.week, "label": item.label, "samples_required": int(item.samples_required or DEFAULT_SAMPLES_REQUIRED)}
            for item in db.query(HandsignDatasetLabel).order_by(HandsignDatasetLabel.week, HandsignDatasetLabel.label).all()
        ],
        "weekly_labels": weekly_label_catalog(db),
        "weeks": available_weeks(db),
        "training": _training_status.copy(),
        "readiness": {
            "can_train": len(complete_labels) >= MIN_TRAINING_LABELS,
            "complete_labels": complete_labels,
            "incomplete_labels": incomplete_labels,
            "minimum_complete_labels": MIN_TRAINING_LABELS,
        },
    }


def save_word_gesture_sample(label: str, week: str | None, images: list[str], db: Session):
    group, target = _group_and_label(label, week, db)
    if len(images) != DEFAULT_SAMPLES_REQUIRED:
        raise ValueError(f"Each recording must contain exactly {DEFAULT_SAMPLES_REQUIRED} frames.")

    import mediapipe as mp
    sequence, detected = [], 0
    with mp.solutions.holistic.Holistic(
        static_image_mode=False, model_complexity=1, smooth_landmarks=True,
        min_detection_confidence=0.3, min_tracking_confidence=0.4,
    ) as holistic:
        for image in images:
            frame = decode_base64_image(image)
            result = holistic.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            if result.pose_landmarks or result.left_hand_landmarks or result.right_hand_landmarks:
                detected += 1
            sequence.append(holistic_result_to_feature_vector(result))

    if detected == 0:
        raise ValueError("No hand or body landmarks were detected. Record the sample again.")

    config = get_handsign_settings()
    directory = config.resolved_word_gesture_dataset_path() / (group or "") / target
    directory.mkdir(parents=True, exist_ok=True)
    sample_number = len(list(directory.glob("*.npz"))) + 1
    path = directory / f"{target.lower()}_{sample_number:04d}.npz"
    np.savez_compressed(path, sequence=np.asarray(sequence, dtype=np.float32), label=target, dataset_group=group or "", frame_feature_length=FRAME_FEATURE_LENGTH)
    requirement = _label_requirements(db).get(target, DEFAULT_SAMPLES_REQUIRED)
    return {"label": target, "week": group, "sample_count": sample_number, "samples_required": requirement, "ready_to_train": sample_number == requirement}


def _complete_sample_paths(dataset_dir, requirements: dict[str, int] | None = None):
    requirements = requirements or {}
    grouped_paths: dict[str, list] = {}
    for path in sorted(dataset_dir.rglob("*.npz")):
        grouped_paths.setdefault(canonical_word(path.parent.name), []).append(path)
    return {
        label: paths for label, paths in grouped_paths.items()
        if len(paths) >= requirements.get(label, DEFAULT_SAMPLES_REQUIRED)
    }


def _job_status_path() -> Path | None:
    return _training_job_dir / "status.json" if _training_job_dir else None


def _remove_training_job() -> None:
    global _training_job_dir
    if _training_job_dir is not None:
        shutil.rmtree(_training_job_dir, ignore_errors=True)
    _training_job_dir = None


def _publish_completed_training() -> None:
    config = get_handsign_settings()
    if _training_job_dir is None:
        raise RuntimeError("Training output is unavailable.")

    trained_model = _training_job_dir / "word_gesture_model.pkl"
    trained_metadata = _training_job_dir / "word_gesture_metadata.json"
    if not trained_model.exists() or not trained_metadata.exists():
        raise RuntimeError("Training finished without complete model output.")

    model_path = config.resolved_word_gesture_model_path()
    metadata_path = config.resolved_word_gesture_metadata_path()
    model_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    trained_model.replace(model_path)
    trained_metadata.replace(metadata_path)


def _refresh_training_status() -> None:
    global _training_process
    with _training_lock:
        process = _training_process
        if process is None:
            return

        status_path = _job_status_path()
        if status_path and status_path.exists():
            try:
                with status_path.open("r", encoding="utf-8") as file:
                    worker_status = json.load(file)
                _training_status.update(worker_status)
            except (OSError, ValueError):
                pass

        if process.poll() is None:
            return

        if _training_status.get("status") == "ready_to_publish":
            try:
                _publish_completed_training()
                _training_status.update(status="completed", message="Word-recognition model trained successfully.")
            except Exception as exc:
                logger.exception("Unable to publish completed word-recognition model")
                _training_status.update(status="failed", message=str(exc))
        elif _training_status.get("status") not in {"failed", "cancelled", "completed"}:
            _training_status.update(status="failed", message="The training worker stopped before completing the model.")

        _training_status["finished_at"] = datetime.now(timezone.utc).isoformat()
        _training_process = None
        _remove_training_job()


def start_training(db: Session):
    global _training_process, _training_job_dir
    with _training_lock:
        if _training_process is not None and _training_process.poll() is None:
            raise RuntimeError("Word-model training is already running.")
        if _training_process is not None:
            _training_process = None
            _remove_training_job()

        config = get_handsign_settings()
        requirements = _label_requirements(db)
        complete_paths = _complete_sample_paths(config.resolved_word_gesture_dataset_path(), requirements)
        if len(complete_paths) < MIN_TRAINING_LABELS:
            raise RuntimeError(
                f"Complete at least {MIN_TRAINING_LABELS} labels using their selected sample targets before training."
            )

        _training_job_dir = Path(tempfile.mkdtemp(prefix="accesslearn-word-training-"))
        job_path = _training_job_dir / "job.json"
        with job_path.open("w", encoding="utf-8") as file:
            json.dump({
                "dataset_dir": str(config.resolved_word_gesture_dataset_path()),
                "model_dir": str(_training_job_dir),
                "sequence_length": config.word_sequence_length,
                "requirements": requirements,
                "tree_count": TRAINING_TREE_COUNT,
            }, file)

        total_samples = sum(map(len, complete_paths.values()))
        _training_status.update(
            status="queued",
            message=f"Preparing {total_samples} samples from {len(complete_paths)} complete labels.",
            started_at=datetime.now(timezone.utc).isoformat(),
            finished_at=None,
            processed_samples=0,
            total_samples=total_samples,
            eligible_labels=len(complete_paths),
            trained_trees=0,
            total_trees=TRAINING_TREE_COUNT,
        )
        backend_root = Path(__file__).resolve().parents[2]
        _training_process = subprocess.Popen(
            [sys.executable, "-m", "services.handsign.word_training_worker", str(job_path)],
            cwd=backend_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return _training_status.copy()


def stop_training() -> dict:
    global _training_process
    with _training_lock:
        process = _training_process
        if process is None or process.poll() is not None:
            raise RuntimeError("No word-model training job is running.")

        _training_status.update(status="stopping", message="Stopping training without saving a new model.")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)

        _training_process = None
        _remove_training_job()
        _training_status.update(
            status="cancelled",
            message="Training was stopped. The previous trained model is still in use.",
            finished_at=datetime.now(timezone.utc).isoformat(),
        )
        return _training_status.copy()
