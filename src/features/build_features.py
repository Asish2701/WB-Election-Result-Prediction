import pandas as pd

from src.config import (
    AC_2021_PATH,
    LS_2019_PATH,
    LS_2024_PATH,
    PC_TO_AC_MAPPING_PATH,
)
from src.data.load_sources import (
    load_ac_2021,
    load_ls_2019,
    load_ls_2024,
    load_pc_to_ac_mapping,
)


def _prepare_ls_features():
    ls_2019 = load_ls_2019(LS_2019_PATH)
    ls_2024 = load_ls_2024(LS_2024_PATH)

    ls_2019 = ls_2019[["PC_Name_Key", "Turnout", "Margin_Pct", "Winner_Party"]].rename(
        columns={
            "Turnout": "LS_2019_Turnout",
            "Margin_Pct": "LS_2019_Margin_Pct",
            "Winner_Party": "LS_2019_Winner_Party",
        }
    )
    ls_2024 = ls_2024[["PC_Name_Key", "Turnout", "Margin_Pct", "Winner_Party"]].rename(
        columns={
            "Turnout": "LS_2024_Turnout",
            "Margin_Pct": "LS_2024_Margin_Pct",
            "Winner_Party": "LS_2024_Winner_Party",
        }
    )

    ls = ls_2019.merge(ls_2024, on="PC_Name_Key", how="outer")
    ls["LS_Turnout_Delta"] = ls["LS_2024_Turnout"] - ls["LS_2019_Turnout"]
    ls["LS_Margin_Delta"] = ls["LS_2024_Margin_Pct"] - ls["LS_2019_Margin_Pct"]
    return ls


def _merge_ls_features(ac_df):
    ls_features = _prepare_ls_features()
    mapping = load_pc_to_ac_mapping(PC_TO_AC_MAPPING_PATH)

    if mapping.empty:
        numeric_cols = [
            "LS_2019_Turnout",
            "LS_2019_Margin_Pct",
            "LS_2024_Turnout",
            "LS_2024_Margin_Pct",
            "LS_Turnout_Delta",
            "LS_Margin_Delta",
        ]
        for col in numeric_cols:
            ac_df[col] = ls_features[col].mean(skipna=True)

        party_cols = ["LS_2019_Winner_Party", "LS_2024_Winner_Party"]
        for col in party_cols:
            mode = ls_features[col].mode(dropna=True)
            ac_df[col] = mode.iloc[0] if not mode.empty else "UNKNOWN"
        ac_df["LS_Features_Mapped"] = 0
        return ac_df

    mapped = mapping.merge(ls_features, on="PC_Name_Key", how="left")
    ac_df = ac_df.merge(mapped.drop(columns=["PC_Name", "PC_Name_Key"], errors="ignore"), on="AC_Number", how="left")
    ac_df["LS_Features_Mapped"] = 1
    return ac_df


def build_training_frame():
    ac_df = load_ac_2021(AC_2021_PATH)
    ac_df = _merge_ls_features(ac_df)

    ac_df["Margin_Pct"] = ac_df["Margin_Pct"].fillna(0)
    ac_df["Turnout"] = ac_df["Turnout"].fillna(ac_df["Turnout"].median())
    ac_df["Electors"] = ac_df["Electors"].fillna(ac_df["Electors"].median())
    ac_df["Votes"] = ac_df["Votes"].fillna(ac_df["Votes"].median())

    ac_df["Winner_Party"] = ac_df["Winner_Party"].fillna("UNKNOWN")
    return ac_df


def build_prediction_frame():
    ac_df = load_ac_2021(AC_2021_PATH)
    ac_df = _merge_ls_features(ac_df)

    ac_df["Turnout"] = ac_df["Turnout"].fillna(ac_df["Turnout"].median())
    ac_df["Electors"] = ac_df["Electors"].fillna(ac_df["Electors"].median())
    ac_df["Votes"] = ac_df["Votes"].fillna(ac_df["Votes"].median())
    ac_df["Margin_Pct"] = ac_df["Margin_Pct"].fillna(0)
    return ac_df
