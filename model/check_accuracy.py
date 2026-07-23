import pickle

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from training_common import (
    CONFIDENCE_THRESHOLD,
    CONFUSION_MATRIX_PATH,
    EXCLUDED_LABELS,
    MODEL_PATH,
    TEST_DIR,
    create_static_hands,
    extract_landmarks,
    feature_length,
)


def main() -> None:
    with MODEL_PATH.open("rb") as file:
        model = pickle.load(file)

    expected_features = getattr(model, "n_features_in_", None)
    if expected_features is not None and expected_features != feature_length():
        raise RuntimeError(
            f"{MODEL_PATH} expects {expected_features} features, but this script produces "
            f"{feature_length()}. Re-run model/2_train_model.py first."
        )

    print("Extracting test landmarks...")
    X_test, y_test = [], []
    failed_by_label = {}
    hands = create_static_hands()
    try:
        for img_path in sorted(TEST_DIR.iterdir()):
            if img_path.suffix.lower() != ".jpg":
                continue

            label = img_path.name.replace("_test.jpg", "")
            if label in EXCLUDED_LABELS:
                continue

            landmarks = extract_landmarks(img_path, hands)
            if landmarks is not None:
                X_test.append(landmarks)
                y_test.append(label)
            else:
                failed_by_label[label] = img_path.name
    finally:
        hands.close()

    X_test = np.asarray(X_test, dtype=np.float32)
    y_test = np.asarray(y_test)

    if len(X_test) == 0:
        raise RuntimeError("No test landmarks were extracted.")

    print(f"Detected hands in {len(X_test)} test images; failed detections: {len(failed_by_label)}")
    if failed_by_label:
        print("Failed hand detections:")
        for label, filename in sorted(failed_by_label.items()):
            print(f"{label:>7}: {filename}")

    y_pred = model.predict(X_test)
    proba = model.predict_proba(X_test)
    confidence = np.max(proba, axis=1)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n{'=' * 40}")
    print(f"  Detected-image test accuracy: {accuracy:.2%}")
    print(f"{'=' * 40}")
    print("This test folder has one sample per class; use it as a smoke test, not a reliability score.\n")

    print("=== Per Class Smoke-Test Result ===")
    labels = sorted(set(y_test) | set(model.classes_) | set(failed_by_label))
    for label in labels:
        if label in failed_by_label:
            print(f"{label:>7}: FAILED_HAND_DETECTION confidence=0%")
            continue

        indices = np.where(y_test == label)[0]
        if len(indices) == 0:
            continue
        i = int(indices[0])
        status = "OK" if y_pred[i] == y_test[i] else f"predicted {y_pred[i]}"
        gate = "pass" if confidence[i] >= CONFIDENCE_THRESHOLD else "below threshold"
        print(f"{label:>7}: {status:>12} confidence={confidence[i]:.0%} {gate}")

    print("\n=== Full Classification Report ===")
    print(classification_report(y_test, y_pred, labels=labels, zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=labels)
    plt.figure(figsize=(15, 12))
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=labels, yticklabels=labels, cmap="Blues")
    plt.title(f"One-Image Test Confusion Matrix (Accuracy: {accuracy:.2%})")
    plt.ylabel("Actual")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(CONFUSION_MATRIX_PATH)
    plt.close()
    print(f"Confusion matrix saved to {CONFUSION_MATRIX_PATH}")


if __name__ == "__main__":
    main()
