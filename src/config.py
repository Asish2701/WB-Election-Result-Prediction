from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODEL_DIR = PROJECT_ROOT / "models"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

AC_2021_PATH = RAW_DIR / "IndiaVotes_AC__West_Bengal_2021.csv"
LS_2019_PATH = RAW_DIR / "IndiaVotes_LS_WB_2019.csv"
LS_2024_PATH = RAW_DIR / "IndiaVotes_LS_WB_2024.csv"

# Optional inputs
CANDIDATE_FEATURES_PATH = RAW_DIR / "candidate_profile_features.csv"
PC_TO_AC_MAPPING_PATH = RAW_DIR / "pc_to_ac_mapping.csv"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
