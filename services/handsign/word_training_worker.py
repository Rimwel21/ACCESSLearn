"""Runs word-gesture training outside the web server so it can be stopped safely."""

import json
import os
import pickle
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.ensemble import ExtraTreesClassifier

from utils.handsign.science_vocabulary import canonical_word
from utils.handsign.word_gesture_features import FEATURE_VERSION, FRAME_FEATURE_LENGTH, resample_sequence


def write_status(path: Path, **changes) -> None:
    current = {}
    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as file:
                current = json.load(file)
        except (OSError, ValueError):
            current = {}
    current.update(changes)
    temporary_path = path.with_suffix(".tmp")
    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(current, file)
    temporary_path.replace(path)


def complete_sample_paths(dataset_dir: Path, requirements: dict[str, int]) -> dict[str, list[Path]]:
    grouped_paths: dict[str, list[Path]] = {}
    for path in sorted(dataset_dir.rglob("*.npz")):
        grouped_paths.setdefault(canonical_word(path.parent.name), []).append(path)
    return {
        label: paths for label, paths in grouped_paths.items()
        if len(paths) >= requirements.get(label, 40)
    }


def train(job_path: Path) -> None:
    with job_path.open("r", encoding="utf-8") as file:
        job = json.load(file)

    output_dir = Path(job["model_dir"])
    status_path = output_dir / "status.json"
    dataset_dir = Path(job["dataset_dir"])
    requirements = {str(key): int(value) for key, value in job["requirements"].items()}
    sequence_length = int(job["sequence_length"])
    tree_count = int(job["tree_count"])

    try:
        paths_by_label = complete_sample_paths(dataset_dir, requirements)
        sample_paths = [path for paths in paths_by_label.values() for path in paths]
        if len(paths_by_label) < 2:
            raise ValueError("At least two labels must meet their selected sample targets before training.")

        write_status(
            status_path,
            status="training",
            message="Loading complete word-sign samples.",
            processed_samples=0,
            total_samples=len(sample_paths),
            eligible_labels=len(paths_by_label),
            trained_trees=0,
            total_trees=tree_count,
        )

        features, labels = [], []
        for index, path in enumerate(sample_paths, start=1):
            data = np.load(path)
            features.append(resample_sequence(data["sequence"], sequence_length).reshape(-1))
            labels.append(canonical_word(str(data["label"].item())))
            if index == len(sample_paths) or index % 25 == 0:
                write_status(
                    status_path,
                    message=f"Preparing samples: {index}/{len(sample_paths)}.",
                    processed_samples=index,
                )

        counts = Counter(labels)
        if len(counts) < 2:
            raise ValueError("At least two labels must meet their selected sample targets before training.")

        write_status(
            status_path,
            message=f"Training {tree_count} trees with {len(features)} samples across {len(counts)} labels.",
        )
        model = ExtraTreesClassifier(
            n_estimators=1,
            max_features="sqrt",
            class_weight="balanced",
            random_state=42,
            n_jobs=min(2, max(1, os.cpu_count() or 1)),
            warm_start=True,
        )
        feature_array = np.asarray(features, dtype=np.float32)
        label_array = np.asarray(labels)
        tree_step = min(25, tree_count)
        for completed_tree_count in range(tree_step, tree_count + tree_step, tree_step):
            target_tree_count = min(completed_tree_count, tree_count)
            model.set_params(n_estimators=target_tree_count)
            model.fit(feature_array, label_array)
            write_status(
                status_path,
                message=f"Training trees: {target_tree_count}/{tree_count}.",
                trained_trees=target_tree_count,
                total_trees=tree_count,
            )
            if target_tree_count == tree_count:
                break

        write_status(status_path, message="Finalizing the trained model.")
        with (output_dir / "word_gesture_model.pkl").open("wb") as file:
            pickle.dump(model, file)
        with (output_dir / "word_gesture_metadata.json").open("w", encoding="utf-8") as file:
            json.dump({
                "feature_version": FEATURE_VERSION,
                "frame_feature_length": FRAME_FEATURE_LENGTH,
                "sequence_length": sequence_length,
                "classes": list(model.classes_),
                "sample_counts": dict(sorted(counts.items())),
                "training_tree_count": tree_count,
                "trained_at": datetime.now(timezone.utc).isoformat(),
            }, file, indent=2)
        write_status(status_path, status="ready_to_publish", message="Publishing the trained word-recognition model.")
    except Exception as exc:
        write_status(status_path, status="failed", message=str(exc), finished_at=datetime.now(timezone.utc).isoformat())


if __name__ == "__main__":
    train(Path(sys.argv[1]))
