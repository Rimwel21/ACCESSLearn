"""Evaluate the active landmark RandomForest model.

The backend uses model/sign_model.pkl, not the legacy Keras image model.
This script is aligned with check_accuracy.py and live backend preprocessing so
offline results match real-time inference.
"""

from pathlib import Path
import runpy


if __name__ == "__main__":
    runpy.run_path(str(Path(__file__).with_name("check_accuracy.py")), run_name="__main__")
