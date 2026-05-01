import pandas as pd

from src.config import PROCESSED_DIR
from src.features.build_features import build_training_frame

OUTPUT_PATH = PROCESSED_DIR / "wb_2021_features.csv"


def build():
    df = build_training_frame()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Processed feature set saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
