import json
import pickle
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from training_common import (
    AFFECTED_LABELS,
    CONFIDENCE_THRESHOLD,
    CONFUSION_MATRIX_PATH,
    EXCLUDED_LABELS,
    METADATA_PATH,
    MIN_DETECTION_CONFIDENCE,
    MODEL_DIR,
    MODEL_PATH,
    TEST_DIR,
    TRAIN_DIR,
    create_static_hands,
    extract_landmarks,
    feature_length,
)
from utils.handsign.landmark_features import FEATURE_VERSION


VALIDATION_SIZE = 0.20
RANDOM_STATE = 42


def load_training_features():
    print("Extracting landmarks from training images...")
    features, labels = [], []
    failed_by_label = Counter()
    total_by_label = Counter()
    hands = create_static_hands()
    try:
        for label_dir in sorted(path for path in TRAIN_DIR.iterdir() if path.is_dir()):
            label = label_dir.name
            if label in EXCLUDED_LABELS:
                continue

            for img_path in sorted(path for path in label_dir.iterdir() if path.is_file()):
                total_by_label[label] += 1
                row = extract_landmarks(img_path, hands)
                if row is None:
                    failed_by_label[label] += 1
                    continue

                features.append(row)
                labels.append(label)
    finally:
        hands.close()

    print(f"Train samples with hands: {len(features)}")
    print(f"Failed hand detections: {sum(failed_by_label.values())}")
    return np.asarray(features, dtype=np.float32), np.asarray(labels), total_by_label, failed_by_label


def load_single_image_test_features():
    features, labels = [], []
    if not TEST_DIR.is_dir():
        return np.empty((0, feature_length()), dtype=np.float32), np.asarray(labels)

    hands = create_static_hands()
    try:
        for img_path in sorted(TEST_DIR.iterdir()):
            if img_path.suffix.lower() != ".jpg":
                continue

            label = img_path.name.replace("_test.jpg", "")
            if label in EXCLUDED_LABELS:
                continue

            row = extract_landmarks(img_path, hands)
            if row is not None:
                features.append(row)
                labels.append(label)
    finally:
        hands.close()

    return np.asarray(features, dtype=np.float32), np.asarray(labels)


def print_low_confidence_classes(model, X, y, title):
    proba = model.predict_proba(X)
    pred_idx = np.argmax(proba, axis=1)
    confidence = np.max(proba, axis=1)
    pred_labels = model.classes_[pred_idx]

    rows = []
    for label in sorted(set(y)):
        mask = y == label
        correct = pred_labels[mask] == y[mask]
        rows.append((label, float(np.mean(correct)), float(np.mean(confidence[mask])), int(np.sum(mask))))

    threshold_percent = int(CONFIDENCE_THRESHOLD * 100)
    print(f"\n=== {title}: classes below {threshold_percent}% mean confidence or 90% accuracy ===")
    weak_rows = [row for row in rows if row[1] < 0.90 or row[2] < CONFIDENCE_THRESHOLD]
    if not weak_rows:
        print("No weak classes found in this split.")
        return

    for label, accuracy, mean_conf, count in weak_rows:
        print(f"{label:>7}: accuracy={accuracy:.1%} mean_confidence={mean_conf:.1%} samples={count}")


def print_affected_class_diagnostics(model, X, y, title):
    proba = model.predict_proba(X)
    pred_idx = np.argmax(proba, axis=1)
    confidence = np.max(proba, axis=1)
    pred_labels = model.classes_[pred_idx]

    print(f"\n=== {title}: affected class diagnostics ===")
    for label in sorted(AFFECTED_LABELS):
        mask = y == label
        if not np.any(mask):
            continue

        correct = pred_labels[mask] == label
        confused = Counter(pred_labels[mask][~correct])
        top_confusions = ", ".join(f"{name}:{count}" for name, count in confused.most_common(4))
        if not top_confusions:
            top_confusions = "none"

        print(
            f"{label:>2}: accuracy={np.mean(correct):.1%} "
            f"mean_confidence={np.mean(confidence[mask]):.1%} "
            f"low_conf_under_{int(CONFIDENCE_THRESHOLD * 100)}="
            f"{np.mean(confidence[mask] < CONFIDENCE_THRESHOLD):.1%} "
            f"confused_with={top_confusions}"
        )


def print_detection_coverage(total_by_label, failed_by_label):
    print("\n=== MediaPipe Detection Coverage ===")
    for label in sorted(total_by_label):
        total = total_by_label[label]
        failed = failed_by_label[label]
        fail_rate = failed / total if total else 0.0
        if label in AFFECTED_LABELS or fail_rate >= 0.20:
            kept = total - failed
            print(f"{label:>7}: kept={kept:5d} failed={failed:5d} fail_rate={fail_rate:.1%}")


def save_confusion_matrix(y_true, y_pred, labels, output_path):
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    plt.figure(figsize=(15, 12))
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=labels, yticklabels=labels, cmap="Blues")
    plt.title("Validation Confusion Matrix")
    plt.ylabel("Actual")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main() -> None:
    X, y, total_by_label, failed_by_label = load_training_features()
    if len(X) == 0:
        raise RuntimeError("No training landmarks were extracted.")

    print_detection_coverage(total_by_label, failed_by_label)

    X_train, X_val, y_train, y_val = train_test_split(
        X,
        y,
        test_size=VALIDATION_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    print("Training model...")
    model = RandomForestClassifier(
        n_estimators=700,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        class_weight="balanced_subsample",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    labels_list = sorted(model.classes_)
    y_val_pred = model.predict(X_val)
    print(f"\nValidation accuracy: {accuracy_score(y_val, y_val_pred):.2%}")
    print("\n=== Validation Classification Report ===")
    print(classification_report(y_val, y_val_pred, labels=labels_list, zero_division=0))
    print_low_confidence_classes(model, X_val, y_val, "Validation")
    print_affected_class_diagnostics(model, X_val, y_val, "Validation")

    X_test, y_test = load_single_image_test_features()
    if len(X_test):
        y_test_pred = model.predict(X_test)
        print(f"\nOne-image test accuracy: {accuracy_score(y_test, y_test_pred):.2%}")
        print("This folder has only one sample per class, so treat it as a smoke test.")
        print(classification_report(y_test, y_test_pred, labels=labels_list, zero_division=0))
        print_low_confidence_classes(model, X_test, y_test, "One-image test")
        print_affected_class_diagnostics(model, X_test, y_test, "One-image test")

    save_confusion_matrix(y_val, y_val_pred, labels_list, CONFUSION_MATRIX_PATH)
    print(f"Confusion matrix saved to {CONFUSION_MATRIX_PATH}")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("wb") as file:
        pickle.dump(model, file)

    metadata = {
        "feature_version": FEATURE_VERSION,
        "feature_length": feature_length(),
        "classes": labels_list,
        "validation_size": VALIDATION_SIZE,
        "random_state": RANDOM_STATE,
        "min_detection_confidence": MIN_DETECTION_CONFIDENCE,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "excluded_labels": sorted(EXCLUDED_LABELS),
        "affected_labels": sorted(AFFECTED_LABELS),
        "train_counts": dict(sorted(Counter(y).items())),
        "raw_file_counts": dict(sorted(total_by_label.items())),
        "failed_detection_counts": dict(sorted(failed_by_label.items())),
    }
    with METADATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2)

    print(f"Model saved to {MODEL_PATH}")
    print(f"Metadata saved to {METADATA_PATH}")


if __name__ == "__main__":
    main()
