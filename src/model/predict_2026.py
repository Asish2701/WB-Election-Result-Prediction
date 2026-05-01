import pandas as pd
import joblib

from src.config import MODEL_DIR, OUTPUT_DIR
from src.features.build_features import build_prediction_frame

MODEL_PATH = MODEL_DIR / "wb_2026_xgb_party_classifier.joblib"
OUTPUT_PATH = OUTPUT_DIR / "wb_2026_predictions.csv"


def predict():
    df = build_prediction_frame()

    artifact = joblib.load(MODEL_PATH)
    pipeline = artifact["pipeline"]
    label_encoder = artifact["label_encoder"]

    feature_cols = [
        "AC_Number",
        "Type",
        "District",
        "Electors",
        "Votes",
        "Turnout",
        "Margin_Pct",
        "LS_2019_Turnout",
        "LS_2019_Margin_Pct",
        "LS_2024_Turnout",
        "LS_2024_Margin_Pct",
        "LS_Turnout_Delta",
        "LS_Margin_Delta",
        "LS_Features_Mapped",
    ]
    for col in feature_cols:
        if col not in df.columns:
            df[col] = pd.NA

    X = df[feature_cols]

    probs = pipeline.predict_proba(X)
    class_labels = label_encoder.inverse_transform(pipeline.named_steps["model"].classes_)
    prob_df = pd.DataFrame(probs, columns=[f"P_{cls}" for cls in class_labels])

    result = pd.concat(
        [
            df[["AC_Number", "Constituency_Name", "District", "Type"]].reset_index(drop=True),
            prob_df,
        ],
        axis=1,
    )

    result["Predicted_Winner"] = prob_df.idxmax(axis=1).str.replace("P_", "", regex=False)
    result["Predicted_Winner_Prob"] = prob_df.max(axis=1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False)

    print(f"Predictions saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    predict()
