import json
import pickle
import threading
from collections import Counter
from datetime import datetime, timezone

import cv2
import numpy as np

from core.handsign_config import get_handsign_settings
from utils.handsign.image import decode_base64_image
from utils.handsign.science_vocabulary import SUPPORTED_SCIENCE_SIGNS, WEEKLY_SCIENCE_SIGN_LABELS, canonical_word
from utils.handsign.word_gesture_features import FEATURE_VERSION, FRAME_FEATURE_LENGTH, holistic_result_to_feature_vector, resample_sequence

SAMPLES_REQUIRED = 40
_training_lock = threading.Lock()
_training_status = {"status": "idle", "message": "No training job has started yet.", "started_at": None, "finished_at": None}


def _group_and_label(label: str, week: str | None):
    target = canonical_word(label)
    group = canonical_word(week) if week else None
    if target not in SUPPORTED_SCIENCE_SIGNS:
        raise ValueError("Choose a configured science sign label.")
    if group and (group not in WEEKLY_SCIENCE_SIGN_LABELS or target not in WEEKLY_SCIENCE_SIGN_LABELS[group]):
        raise ValueError("That label is not assigned to the selected week.")
    return group, target


def admin_dataset_summary():
    from services.handsign.word_gesture_service import word_gesture_summary
    return {
        **word_gesture_summary(),
        "samples_required": SAMPLES_REQUIRED,
        "weekly_labels": WEEKLY_SCIENCE_SIGN_LABELS,
        "training": _training_status.copy(),
    }


def save_word_gesture_sample(label: str, week: str | None, images: list[str]):
    group, target = _group_and_label(label, week)
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
