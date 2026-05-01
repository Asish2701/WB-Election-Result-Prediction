import pandas as pd


def _clean_numeric(value):
    if pd.isna(value):
        return pd.NA
    text = str(value).replace(",", "").strip()
    if text.endswith("%"):
        text = text[:-1]
    if text == "":
        return pd.NA
    return pd.to_numeric(text, errors="coerce")


def load_ac_2021(path):
    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "AC Name": "Constituency_Name",
            "AC No.": "AC_Number",
            "Winning Candidate": "Winner_Candidate",
            "Party": "Winner_Party",
            "Total Electors": "Electors",
            "Total Votes": "Votes",
            "Poll%": "Turnout",
            "Margin": "Margin",
            "Margin %": "Margin_Pct",
        }
    )

    for col in ["Electors", "Votes", "Turnout", "Margin", "Margin_Pct"]:
        if col in df.columns:
            df[col] = df[col].map(_clean_numeric)

    df["Year"] = 2021
    df["AC_Number"] = pd.to_numeric(df["AC_Number"], errors="coerce")
    return df


def _load_ls_generic(path, year):
    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "PC Name": "PC_Name",
            "Winning Candidate": "Winner_Candidate",
            "Party": "Winner_Party",
            "Electors": "Electors",
            "Votes": "Votes",
            "Turnout": "Turnout",
            "Margin": "Margin",
            "Margin %": "Margin_Pct",
        }
    )
    for col in ["Electors", "Votes", "Turnout", "Margin", "Margin_Pct"]:
        if col in df.columns:
            df[col] = df[col].map(_clean_numeric)

    df["Year"] = year
    df["PC_Name_Key"] = df["PC_Name"].astype(str).str.strip().str.upper()
    return df


def load_ls_2019(path):
    return _load_ls_generic(path, 2019)


def load_ls_2024(path):
    return _load_ls_generic(path, 2024)


def load_candidate_features(path):
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    return df


def load_pc_to_ac_mapping(path):
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    required = {"AC_Number", "PC_Name"}
    if not required.issubset(set(df.columns)):
        raise ValueError("Mapping file must contain AC_Number and PC_Name")
    df["AC_Number"] = pd.to_numeric(df["AC_Number"], errors="coerce")
    df["PC_Name_Key"] = df["PC_Name"].astype(str).str.strip().str.upper()
    return df
