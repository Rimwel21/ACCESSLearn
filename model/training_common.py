import sys
from pathlib import Path

import cv2


ACCESSLEARN_ROOT = Path(__file__).resolve().parents[1]
if str(ACCESSLEARN_ROOT) not in sys.path:
    sys.path.insert(0, str(ACCESSLEARN_ROOT))

from core import handsign_recognition as recognition  # noqa: E402
from utils.handsign.landmark_features import feature_length, landmarks_to_feature_vector  # noqa: E402


DATASET_ROOT = ACCESSLEARN_ROOT / "dataset" / "ASL_Alphabet_Dataset"
TRAIN_DIR = DATASET_ROOT / "asl_alphabet_train"
TEST_DIR = DATASET_ROOT / "asl_alphabet_test"
MODEL_DIR = ACCESSLEARN_ROOT / "model"
MODEL_PATH = MODEL_DIR / "sign_model.pkl"
METADATA_PATH = MODEL_DIR / "sign_model_metadata.json"
CONFUSION_MATRIX_PATH = MODEL_DIR / "confusion_matrix.png"
LANDMARKS_CSV_PATH = MODEL_DIR / "landmarks.csv"

MIN_DETECTION_CONFIDENCE = recognition.LANDMARK_DETECTION_CONFIDENCE
CONFIDENCE_THRESHOLD = recognition.CONFIDENCE_THRESHOLD
EXCLUDED_LABELS = {"nothing"}
AFFECTED_LABELS = set(recognition.PROBLEM_LABELS) | {"G", "M", "N", "O"}


def create_static_hands():
    import mediapipe as mp

    return mp.solutions.hands.Hands(
        static_image_mode=True,
        max_num_hands=1,
        min_detection_confidence=MIN_DETECTION_CONFIDENCE,
    )


def extract_landmarks(img_path: Path, hands):
    img = cv2.imread(str(img_path))
    if img is None:
        return None

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)
    if not result.multi_hand_landmarks:
        return None

    return landmarks_to_feature_vector(result.multi_hand_landmarks[0].landmark)
