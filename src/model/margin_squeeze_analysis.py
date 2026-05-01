"""
Margin Squeeze Analysis for West Bengal 2026 Elections

Incorporates four major factors that could impact TMC margins:
1. Voter Roll Purge (91 lakh deletions - 140+ constituencies)
2. RG Kar Medical College case (women voter disillusionment)
3. Corruption & lawlessness narrative (industries fleeing, investor confidence)
4. Sandeshkhali aftermath (removal of voter intimidation effect)
"""

import pandas as pd
import numpy as np
from pathlib import Path

from src.config import OUTPUT_DIR, PROCESSED_DIR

CALIBRATED_PATH = OUTPUT_DIR / "wb_2026_calibrated.csv"
AC_2021_PATH = PROCESSED_DIR / "wb_2021_features.csv"
OUTPUT_SQUEEZE_PATH = OUTPUT_DIR / "wb_2026_margin_squeeze_analysis.csv"
OUTPUT_ADJUSTED_PATH = OUTPUT_DIR / "wb_2026_adjusted_for_squeeze.csv"
OUTPUT_SQUEEZE_TALLY = OUTPUT_DIR / "wb_2026_adjusted_tally.csv"


def _load_2021_results():
    """Load 2021 election results to identify high-margin seats and vulnerable districts"""
    df = pd.read_csv(AC_2021_PATH)
    # Keep only unique seats (remove duplicates from candidate-level data)
    df = df.drop_duplicates(subset=["AC_Number"], keep="first")
    return df


def _identify_purge_vulnerable(ac_data):
    """
    Identify constituencies vulnerable to voter roll purge.
    
    Purge affected:
    - Murshidabad: Lost 12.5 lakh voters
    - Maldah: Lost 10+ lakh voters  
    - Uttar Dinajpur: Lost 7+ lakh voters
    - Other border/minority districts
    
    In 140+ constituencies, deleted voters EXCEED 2021 TMC winning margins.
    """
    purge_vulnerable_districts = {
        "Murshidabad": 0.35,    # 35% margin squeeze in vulnerable seats
        "Maldah": 0.30,         # High impact
        "Uttar Dinajpur": 0.28,
        "Dakshin Dinajpur": 0.15,
    }
    
    ac_data["purge_squeeze"] = ac_data["District"].map(purge_vulnerable_districts).fillna(0.05)
    return ac_data


def _identify_rgkar_vulnerable(ac_data):
    """
    RG Kar case impact: Symbolic candidacy (Ratna Debnath - victim's mother) from Panihati (AC 111).
    
    Impact: Disillusionment among women voters, traditionally core TMC support
    - Panihati (AC 111) and neighboring constituencies: High impact
    - Urban constituencies with high female voter ratio: Moderate impact
    - Rural areas: Lower impact
    
    Women are ~49% of voters; if 3-5% shift towards BJP, that's significant for tight seats.
    """
    # Panihati AC number is 111
    ac_data["is_panihati"] = ac_data["AC_Number"] == 111
    ac_data["is_kolkata_urban"] = ac_data["District"].isin(["Kolkata", "North Twenty Four Parganas", "South  Twenty Four Parganas"])
    
    rgkar_squeeze = np.where(
        ac_data["is_panihati"],
        0.12,  # Panihati: 12% squeeze from women voter shift
        np.where(
            ac_data["is_kolkata_urban"],
            0.05,  # Urban: 5% squeeze
            0.02   # Rural: 2% squeeze
        )
    )
    ac_data["rgkar_squeeze"] = rgkar_squeeze
    return ac_data


def _identify_corruption_narrative_vulnerable(ac_data):
    """
    Corruption & lawlessness narrative impact.
    
    Key narrative: "Funeral of law & order" - gherao of judicial officers in Maldah,
    industries/investors fleeing, "cut money culture"
    
    This particularly impacts:
    - Industrial areas: Asansol, Durgapur regions (Barddhaman)
    - Maldah (where gherao occurred)
    - Business/trading constituencies
    """
    narrative_vulnerable_districts = {
        "Barddhaman": 0.08,     # Industrial base threatened
        "Maldah": 0.12,         # Judicial gherao incident
        "Hugli": 0.06,          # Industrial
        "North Twenty Four Parganas": 0.04,  # Business hub but more diverse
        "Kolkata": 0.03,        # Urban professional class
    }
    
    ac_data["corruption_squeeze"] = ac_data["District"].map(narrative_vulnerable_districts).fillna(0.02)
    return ac_data


def _identify_sandeshkhali_vulnerable(ac_data):
    """
    Sandeshkhali aftermath: Sheikh Shahjahan in jail, removal of voter intimidation.
    
    Impact: Voters previously intimidated can now vote freely.
    - This helps opposition (BJP) in riverine constituencies
    - Sandeshkhali (AC 123), Basirhat region, other North 24 Parganas riverine areas
    - Primarily benefit BJP (Opposition was intimidated before)
    """
    # Sandeshkhali-specific impact
    ac_data["is_sandeshkhali"] = ac_data["AC_Number"] == 123
    
    riverine_districts = {
        "North Twenty Four Parganas": 0.08,  # Highest impact - epicenter of Sandeshkhali
        "South  Twenty Four Parganas": 0.04,   # Some riverine areas (note: extra spaces in district name)
    }
    
    # Base squeeze from riverine district
    sandeshkhali_squeeze = ac_data["District"].map(riverine_districts).fillna(0.01)
    
    # Amplify for Sandeshkhali itself
    sandeshkhali_squeeze = np.where(
        ac_data["is_sandeshkhali"],
        0.15,  # Sandeshkhali gets 15% squeeze
        sandeshkhali_squeeze
    )
    
    ac_data["sandeshkhali_squeeze"] = sandeshkhali_squeeze
    return ac_data


def _aggregate_squeeze_factor(ac_data):
    """
    Aggregate all squeeze factors.
    
    Total squeeze = sum of individual factors, capped at max realistic margin loss.
    We apply this as a multiplicative adjustment to TMC probability and 
    multiplicative boost to BJP probability.
    """
    squeeze_cols = ["purge_squeeze", "rgkar_squeeze", "corruption_squeeze", "sandeshkhali_squeeze"]
    ac_data["total_squeeze_pct"] = ac_data[squeeze_cols].sum(axis=1)
    
    # Cap squeeze at 25% for any single constituency (realism check)
    ac_data["total_squeeze_pct"] = ac_data["total_squeeze_pct"].clip(upper=0.25)
    
    return ac_data


def analyze_squeeze():
    """Generate margin squeeze analysis report"""
    ac_2021 = _load_2021_results()
    
    # Build squeeze factors
    ac_2021 = _identify_purge_vulnerable(ac_2021)
    ac_2021 = _identify_rgkar_vulnerable(ac_2021)
    ac_2021 = _identify_corruption_narrative_vulnerable(ac_2021)
    ac_2021 = _identify_sandeshkhali_vulnerable(ac_2021)
    ac_2021 = _aggregate_squeeze_factor(ac_2021)
    
    analysis = ac_2021[[
        "AC_Number",
        "Constituency_Name",
        "District",
        "Margin_Pct",
        "purge_squeeze",
        "rgkar_squeeze",
        "corruption_squeeze",
        "sandeshkhali_squeeze",
        "total_squeeze_pct"
    ]].copy()
    
    # Identify highest-risk constituencies
    analysis = analysis.sort_values("total_squeeze_pct", ascending=False)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    analysis.to_csv(OUTPUT_SQUEEZE_PATH, index=False)
    print(f"Margin squeeze analysis saved: {OUTPUT_SQUEEZE_PATH}")
    
    return analysis, ac_2021


def apply_squeeze_adjustments(calibrated_df, squeeze_factors_df):
    """
    Apply squeeze factors to calibrated probabilities.
    
    Logic:
    - Reduce TMC probability by factor corresponding to squeeze percentage
    - Increase BJP probability as beneficiary
    - Maintain normalization
    """
    adjusted = calibrated_df.copy()
    
    # Merge squeeze factors
    squeeze_lookup = squeeze_factors_df[["AC_Number", "total_squeeze_pct"]].set_index("AC_Number")
    adjusted["squeeze_pct"] = adjusted["AC_Number"].map(
        lambda x: squeeze_lookup.loc[x, "total_squeeze_pct"] if x in squeeze_lookup.index else 0
    )
    
    # Get probability columns
    tmc_col = "P_All India Trinamool Congress"
    bjp_col = "P_Bharatiya Janta Party"
    other_col = "P_OTHER"
    
    # Apply squeeze: reduce TMC, boost BJP
    # If squeeze is 10%, reduce TMC by 10% of its current prob, 
    # and distribute that reduction 70% to BJP, 30% to OTHER
    for idx, row in adjusted.iterrows():
        squeeze = row["squeeze_pct"]
        tmc_reduction = adjusted.loc[idx, tmc_col] * squeeze
        
        adjusted.loc[idx, tmc_col] -= tmc_reduction * 0.70
        adjusted.loc[idx, bjp_col] += tmc_reduction * 0.70
        adjusted.loc[idx, other_col] += tmc_reduction * 0.30
    
    # Renormalize probabilities
    prob_cols = [tmc_col, bjp_col, other_col]
    total = adjusted[prob_cols].sum(axis=1)
    adjusted[prob_cols] = adjusted[prob_cols].div(total, axis=0)
    
    # Update predicted winner
    adjusted["Predicted_Winner"] = adjusted[prob_cols].idxmax(axis=1).str.replace("P_", "")
    adjusted["Predicted_Winner_Prob"] = adjusted[prob_cols].max(axis=1)
    
    # Ensure squeeze_pct is preserved in output
    adjusted["squeeze_pct"] = adjusted["squeeze_pct"]
    
    return adjusted


def generate_adjusted_predictions():
    """Generate margin-squeeze-adjusted predictions"""
    print("Loading calibrated predictions...")
    calibrated = pd.read_csv(CALIBRATED_PATH)
    
    print("Analyzing margin squeeze factors...")
    squeeze_analysis, squeeze_factors = analyze_squeeze()
    
    print("Applying squeeze adjustments...")
    adjusted = apply_squeeze_adjustments(calibrated, squeeze_factors)
    
    # Save adjusted predictions with all relevant columns
    adjusted_cols = [
        "AC_Number", "Constituency_Name", "District", "Type",
        "Predicted_Winner", "Predicted_Winner_Prob",
        "P_All India Trinamool Congress", "P_Bharatiya Janta Party", "P_OTHER",
        "squeeze_pct"
    ]
    
    # Select only columns that exist
    cols_to_save = [col for col in adjusted_cols if col in adjusted.columns]
    adjusted[cols_to_save].to_csv(OUTPUT_ADJUSTED_PATH, index=False)
    print(f"Adjusted predictions saved: {OUTPUT_ADJUSTED_PATH}")
    
    # Generate adjusted tally
    adjusted_tally = (
        adjusted["Predicted_Winner"]
        .value_counts()
        .rename_axis("Party")
        .reset_index(name="Seats")
        .sort_values("Seats", ascending=False)
    )
    adjusted_tally.to_csv(OUTPUT_SQUEEZE_TALLY, index=False)
    print(f"Adjusted tally saved: {OUTPUT_SQUEEZE_TALLY}")
    print(f"\nAdjusted Tally:\n{adjusted_tally}")
    
    return adjusted, squeeze_analysis


def generate_flip_risk_report(adjusted_df, baseline_df):
    """
    Identify constituencies that flip winner from baseline to adjusted predictions.
    These are the highest-risk seats under margin squeeze scenario.
    """
    flip_analysis = pd.merge(
        baseline_df[["AC_Number", "Constituency_Name", "District", "Predicted_Winner", "Predicted_Winner_Prob"]],
        adjusted_df[["AC_Number", "Predicted_Winner", "Predicted_Winner_Prob"]],
        on="AC_Number",
        suffixes=("_baseline", "_adjusted")
    )
    
    flip_analysis["flip"] = flip_analysis["Predicted_Winner_baseline"] != flip_analysis["Predicted_Winner_adjusted"]
    
    flips = flip_analysis[flip_analysis["flip"]].sort_values("Predicted_Winner_Prob_adjusted")
    
    OUTPUT_FLIPS_PATH = OUTPUT_DIR / "wb_2026_squeeze_flips.csv"
    flips.to_csv(OUTPUT_FLIPS_PATH, index=False)
    print(f"\nSeats that flip under margin squeeze scenario: {len(flips)}")
    print(flips[["Constituency_Name", "District", "Predicted_Winner_baseline", "Predicted_Winner_adjusted", "Predicted_Winner_Prob_adjusted"]].head(20))
    
    return flips


if __name__ == "__main__":
    adjusted, squeeze_analysis = generate_adjusted_predictions()
    
    # Compare with baseline
    calibrated = pd.read_csv(CALIBRATED_PATH)
    flips = generate_flip_risk_report(calibrated, adjusted)
