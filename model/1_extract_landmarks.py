import csv

from training_common import (
    EXCLUDED_LABELS,
    LANDMARKS_CSV_PATH,
    TRAIN_DIR,
    create_static_hands,
    extract_landmarks,
    feature_length,
)


def main() -> None:
    hands = create_static_hands()
    try:
        with LANDMARKS_CSV_PATH.open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            header = [f"feature_{i}" for i in range(feature_length())] + ["label"]
            writer.writerow(header)

            written = 0
            failed = 0
            for label_dir in sorted(path for path in TRAIN_DIR.iterdir() if path.is_dir()):
                label = label_dir.name
                if label in EXCLUDED_LABELS:
                    continue

                for img_path in sorted(path for path in label_dir.iterdir() if path.is_file()):
                    row = extract_landmarks(img_path, hands)
                    if row is None:
                        failed += 1
                        continue

                    writer.writerow(row + [label])
                    written += 1

        print(
            f"Landmark extraction complete: {written} rows written to "
            f"{LANDMARKS_CSV_PATH}, {failed} failed detections."
        )
    finally:
        hands.close()


if __name__ == "__main__":
    main()
