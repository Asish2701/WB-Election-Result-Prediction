import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
from xgboost import XGBClassifier

from src.config import MODEL_DIR, OUTPUT_DIR
from src.features.build_features import build_training_frame

MODEL_PATH = MODEL_DIR / "wb_2026_xgb_party_classifier.joblib"
METRICS_PATH = OUTPUT_DIR / "training_metrics.json"


def train():
    df = build_training_frame()

    target = "Winner_Party"
    party_counts = df[target].value_counts(dropna=False)
    rare_parties = party_counts[party_counts < 2].index
    if len(rare_parties) > 0:
        df[target] = df[target].where(~df[target].isin(rare_parties), "OTHER")

    y = df[target]
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

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
            df[col] = np.nan

    X = df[feature_cols]

    categorical_cols = ["Type", "District"]
    numeric_cols = [col for col in feature_cols if col not in categorical_cols]

    preprocessor = ColumnTransformer(
        transformers=[
            ("categorical", OneHotEncoder(handle_unknown="ignore"), categorical_cols),
            ("numeric", "passthrough", numeric_cols),
        ]
    )

    model = XGBClassifier(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", model),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    pipeline.fit(X_train, y_train)
    preds = pipeline.predict(X_test)

    metrics = {
        "accuracy": float(accuracy_score(y_test, preds)),
        "f1_macro": float(f1_score(y_test, preds, average="macro")),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "classes": list(label_encoder.classes_),
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump({"pipeline": pipeline, "label_encoder": label_encoder}, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    print(f"Model saved to: {MODEL_PATH}")
    print(f"Metrics saved to: {METRICS_PATH}")


if __name__ == "__main__":
    train()
