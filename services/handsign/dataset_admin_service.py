import json
import pickle
import threading
from collections import Counter
from datetime import datetime, timezone

import cv2
import numpy as np
from sqlalchemy.orm import Session

from core.handsign_config import get_handsign_settings
from models.handsign_dataset_label import HandsignDatasetLabel
from models.handsign_dataset_week import HandsignDatasetWeek
from utils.handsign.image import decode_base64_image
from utils.handsign.science_vocabulary import SUPPORTED_SCIENCE_SIGNS, WEEKLY_SCIENCE_SIGN_LABELS, canonical_word
from utils.handsign.word_gesture_features import FEATURE_VERSION, FRAME_FEATURE_LENGTH, holistic_result_to_feature_vector, resample_sequence

SAMPLES_REQUIRED = 40
_training_lock = threading.Lock()
_training_status = {"status": "idle", "message": "No training job has started yet.", "started_at": None, "finished_at": None}


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


def week_labels(week: str, db: Session) -> list[str]:
    return weekly_label_catalog(db).get(normalize_week(week), [])


def _group_and_label(label: str, week: str | None, db: Session):
    target = canonical_word(label)
    group = normalize_week(week)
    if target not in week_labels(group, db):
        raise ValueError("That label is not assigned to the selected week.")
    return group, target


def admin_dataset_summary(db: Session):
    from services.handsign.word_gesture_service import word_gesture_summary
    return {
        **word_gesture_summary(),
        "samples_required": SAMPLES_REQUIRED,
        "weekly_labels": weekly_label_catalog(db),
        "weeks": available_weeks(db),
        "training": _training_status.copy(),
    }


def save_word_gesture_sample(label: str, week: str | None, images: list[str], db: Session):
    group, target = _group_and_label(label, week, db)
    if len(images) != SAMPLES_REQUIRED:
        raise ValueError(f"Each recording must contain exactly {SAMPLES_REQUIRED} frames.")

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
    return {"label": target, "week": group, "sample_count": sample_number, "ready_to_train": sample_number >= SAMPLES_REQUIRED}


def start_training():
    if not _training_lock.acquire(blocking=False):
        raise RuntimeError("Word-model training is already running.")
    _training_status.update(status="queued", message="Training job queued.", started_at=datetime.now(timezone.utc).isoformat(), finished_at=None)
    thread = threading.Thread(target=_train_and_release, daemon=True)
    thread.start()
    return _training_status.copy()


def _train_and_release():
    try:
        _training_status.update(status="training", message="Training the word-recognition model.")
        config = get_handsign_settings()
        features, labels = [], []
        for path in config.resolved_word_gesture_dataset_path().rglob("*.npz"):
            data = np.load(path)
            label = canonical_word(str(data["label"].item()))
            features.append(resample_sequence(data["sequence"], config.word_sequence_length).reshape(-1))
            labels.append(label)
        counts = Counter(labels)
        if not counts:
            raise ValueError("Record at least one complete word-sign sample before training.")

        from sklearn.ensemble import ExtraTreesClassifier
        model = ExtraTreesClassifier(n_estimators=500, max_features="sqrt", class_weight="balanced", random_state=42, n_jobs=-1)
        model.fit(np.asarray(features, dtype=np.float32), np.asarray(labels))
        model_path = config.resolved_word_gesture_model_path()
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, "wb") as file:
            pickle.dump(model, file)
        metadata = {
            "feature_version": FEATURE_VERSION,
            "frame_feature_length": FRAME_FEATURE_LENGTH,
            "sequence_length": config.word_sequence_length,
            "classes": list(model.classes_),
            "sample_counts": dict(sorted(counts.items())),
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(config.resolved_word_gesture_metadata_path(), "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2)
        _training_status.update(status="completed", message="Word-recognition model trained successfully.")
    except Exception as exc:
        _training_status.update(status="failed", message=str(exc))
    finally:
        _training_status["finished_at"] = datetime.now(timezone.utc).isoformat()
        _training_lock.release()
