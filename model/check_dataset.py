from training_common import TRAIN_DIR, TEST_DIR


def main() -> None:
    print("=== Train folders ===")
    counts = {}
    for folder in sorted(TRAIN_DIR.iterdir()):
        if folder.is_dir():
            counts[folder.name] = sum(1 for entry in folder.iterdir() if entry.is_file())

    for label, count in counts.items():
        print(f"{label:>7}: {count} files")

    if counts:
        max_count = max(counts.values())
        print("\n=== Imbalance Check ===")
        for label, count in counts.items():
            ratio = count / max_count
            if ratio < 0.80:
                print(f"{label:>7}: {count} files ({ratio:.0%} of largest class)")

    print("\n=== Test files ===")
    test_files = sorted(name for name in TEST_DIR.iterdir() if name.suffix.lower() == ".jpg")
    print(f"{len(test_files)} JPG files")
    for path in test_files:
        print(f"  {path.name}")

    print("\nNote: this Kaggle-style test folder has about one image per class, so it is only a smoke test.")


if __name__ == "__main__":
    main()
