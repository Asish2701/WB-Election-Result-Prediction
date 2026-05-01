import pandas as pd

from src.config import OUTPUT_DIR, RAW_DIR

BASELINE_PATH = OUTPUT_DIR / "wb_2026_predictions.csv"
CANDIDATE_LIST_PATH = RAW_DIR / "West_Bengal_Election_2026_All_Parties_List.csv"
OUTPUT_PATH = OUTPUT_DIR / "wb_2026_calibrated.csv"
TALLY_PATH = OUTPUT_DIR / "wb_2026_calibrated_tally.csv"

# Calibration settings
SWING_FACTORS = {
    "All India Trinamool Congress": 0.95,
    "Bharatiya Janta Party": 1.25,
    "OTHER": 0.90,
}

EXIT_POLL_TARGETS = {
    "All India Trinamool Congress": 164,
    "Bharatiya Janta Party": 126,
    "OTHER": 4,
}

CANDIDATE_PENALTY = 0.90
PLACEHOLDER_PENALTY = 0.92


def _read_candidates(path):
    if not path.exists():
        return pd.DataFrame()
    try:
        df = pd.read_csv(path)
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")

    df.columns = [col.strip() for col in df.columns]
    base_cols = ["Const. No.", "Constituency Name"]
    party_cols = [col for col in df.columns if col not in base_cols]

    records = []
    for _, row in df.iterrows():
        ac_no = row.get("Const. No.")
        seat = row.get("Constituency Name")
        for col in party_cols:
            party = col.replace("Candidate Name", "").replace("(", "").replace(")", "").strip()
            candidate = row.get(col)
            candidate = "" if pd.isna(candidate) else str(candidate).strip()
            records.append(
                {
                    "AC_Number": ac_no,
                    "Constituency_Name": seat,
                    "Party": party,
                    "Candidate": candidate,
                }
            )

    long_df = pd.DataFrame(records)
    long_df["AC_Number"] = pd.to_numeric(long_df["AC_Number"], errors="coerce")
    return long_df


def _candidate_flags(candidate):
    if candidate is None:
        return 0, 0
    text = str(candidate).strip()
    if text == "":
        return 0, 0
    placeholder = 1 if ("*" in text or "?" in text) else 0
    return 1, placeholder


def _apply_swing(prob_df):
    adjusted = prob_df.copy()
    for party, factor in SWING_FACTORS.items():
        col = f"P_{party}"
        if col in adjusted.columns:
            adjusted[col] = adjusted[col] * factor
    return adjusted


def _apply_exit_poll_targets(prob_df, iterations=4):
    adjusted = prob_df.copy()
    for _ in range(iterations):
        expected = {party: adjusted[f"P_{party}"].sum() for party in EXIT_POLL_TARGETS}
        factors = {
            party: (EXIT_POLL_TARGETS[party] / expected[party]) if expected[party] else 1.0
            for party in EXIT_POLL_TARGETS
        }
        for party, factor in factors.items():
            adjusted[f"P_{party}"] = adjusted[f"P_{party}"] * factor
        adjusted = _renormalize(adjusted)
    return adjusted


def _renormalize(prob_df):
    adjusted = prob_df.copy()
    prob_cols = [col for col in adjusted.columns if col.startswith("P_")]
    total = adjusted[prob_cols].sum(axis=1)
    adjusted[prob_cols] = adjusted[prob_cols].div(total, axis=0)
    return adjusted


def calibrate():
    df = pd.read_csv(BASELINE_PATH)
    prob_cols = [col for col in df.columns if col.startswith("P_")]

    probs = df[prob_cols].copy()
    probs = _apply_swing(probs)
    probs = _renormalize(probs)
    probs = _apply_exit_poll_targets(probs)

    candidates = _read_candidates(CANDIDATE_LIST_PATH)
    if not candidates.empty:
        candidate_map = candidates.set_index(["AC_Number", "Party"])["Candidate"].to_dict()
        presence_flags = []
        placeholder_flags = []
        for _, row in df.iterrows():
            party = row["Predicted_Winner"]
            candidate = candidate_map.get((row["AC_Number"], party), "")
            present, placeholder = _candidate_flags(candidate)
            presence_flags.append(present)
            placeholder_flags.append(placeholder)
            if party in EXIT_POLL_TARGETS:
                col = f"P_{party}"
                if present == 0:
                    probs.loc[row.name, col] = probs.loc[row.name, col] * CANDIDATE_PENALTY
                if placeholder == 1:
                    probs.loc[row.name, col] = probs.loc[row.name, col] * PLACEHOLDER_PENALTY

        probs = _renormalize(probs)
        df["Candidate_Present"] = presence_flags
        df["Candidate_Placeholder"] = placeholder_flags

    calibrated = pd.concat([df.drop(columns=prob_cols), probs], axis=1)
    calibrated["Predicted_Winner"] = probs.idxmax(axis=1).str.replace("P_", "", regex=False)
    calibrated["Predicted_Winner_Prob"] = probs.max(axis=1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    calibrated.to_csv(OUTPUT_PATH, index=False)

    tally = (
        calibrated["Predicted_Winner"]
        .value_counts()
        .rename_axis("Party")
        .reset_index(name="Seats")
    )
    tally.to_csv(TALLY_PATH, index=False)

    print(f"Calibrated predictions saved: {OUTPUT_PATH}")
    print(f"Calibrated tally saved: {TALLY_PATH}")


if __name__ == "__main__":
    calibrate()
