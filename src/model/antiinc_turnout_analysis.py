"""
Anti-Incumbency & Turnout Impact Analysis for West Bengal 2026 Elections

Incorporates:
1. 15-year anti-incumbency sentiment (corruption, governance, "cut money")
2. Required 5.5% swing to fundamentally alter outcome
3. Record 91.5% voter turnout in some phases (change wave indicator)
"""

import pandas as pd
import numpy as np
from pathlib import Path

from src.config import OUTPUT_DIR, PROCESSED_DIR

CALIBRATED_PATH = OUTPUT_DIR / "wb_2026_calibrated.csv"
AC_2021_PATH = PROCESSED_DIR / "wb_2021_features.csv"
ADJUSTED_SQUEEZE_PATH = OUTPUT_DIR / "wb_2026_adjusted_for_squeeze.csv"

OUTPUT_ANTIINC_PATH = OUTPUT_DIR / "wb_2026_antiincumbency_analysis.csv"
OUTPUT_TURNOUT_PATH = OUTPUT_DIR / "wb_2026_turnout_impact.csv"
OUTPUT_SWING_PATH = OUTPUT_DIR / "wb_2026_swing_adjustment.csv"
OUTPUT_COMBINED_PATH = OUTPUT_DIR / "wb_2026_all_factors_combined.csv"
OUTPUT_COMBINED_TALLY = OUTPUT_DIR / "wb_2026_all_factors_tally.csv"


def _load_2021_results():
    """Load 2021 election results"""
    df = pd.read_csv(AC_2021_PATH)
    df = df.drop_duplicates(subset=["AC_Number"], keep="first")
    return df


def _identify_antiincumbency_vulnerable(ac_data):
    """
    Quantify anti-incumbency vulnerability by constituency type.
    
    After 15 years in power, TMC faces:
    - "Cut money culture" allegations (affects trading/business constituencies)
    - Governance failures (administrative/civic constituencies)
    - Corruption perception (urban, educated voters)
    
    Vulnerable voter profiles:
    - Business/trading communities (traditional congress voters, now anti-TMC)
    - Urban professionals (high awareness, cynicism about governance)
    - Young voters (never known non-TMC rule; seeking change)
    """
    
    antiinc_by_district = {
        "Kolkata": 0.12,              # Urban, professional, high political engagement
        "North Twenty Four Parganas": 0.10,  # Metro fringe, business class
        "South  Twenty Four Parganas": 0.10,  # Metro fringe, business class
        "Hugli": 0.08,                # Industrial workers + traders
        "Barddhaman": 0.09,           # Industrial, business centers
        "Haora": 0.10,                # Industrial, trading communities
        "Nadia": 0.06,                # Agricultural; less anti-incumbency exposure
        "Birbhum": 0.05,              # Rural; less governance pressure
        "Murshidabad": 0.07,          # Border district; mixed sentiment
        "Maldah": 0.08,               # Border, governance concerns
        "Uttar Dinajpur": 0.06,       # Border, agricultural
        "Dakshin Dinajpur": 0.06,     # Border
        "Bankura": 0.05,              # Rural, less business exposure
        "Puruliya": 0.04,             # Rural, tribal areas
        "Paschim Medinipur": 0.05,    # Mixed rural-urban
        "Purba Medinipur": 0.06,      # Coastal, some trading
        "Jalpaiguri": 0.05,           # Hill station, less political engagement
        "Darjiling": 0.04,            # Hill communities, distinct politics
        "Koch Bihar": 0.05,           # Border, distinct political dynamics
    }
    
    ac_data["antiinc_squeeze"] = ac_data["District"].map(antiinc_by_district).fillna(0.06)
    return ac_data


def _identify_turnout_impact(ac_data):
    """
    Model impact of record 91.5% turnout in some phases.
    
    High turnout typically correlates with:
    - Anti-incumbency wave (new voters motivated by change desire)
    - Reduced voter apathy (mobilized electorate)
    - Increased female/youth voter participation
    
    Constituency-level impact:
    - Constituencies with historically high turnout (already mobilized): 2% impact
    - Constituencies with historically low turnout (now mobilized): 8% impact
    - Average constituency: 5% impact
    
    Interpretation: Additional voters brought out by record turnout are:
    - 60% likely to be anti-TMC (seeking change)
    - 40% likely to be pro-TMC or undecided
    """
    
    # Use 2021 turnout data as baseline
    ac_data["turnout_2021"] = ac_data["Turnout"]
    
    # Categorize based on historical turnout
    # High turnout (>90%): already mobilized, 2% impact
    # Medium turnout (80-90%): somewhat mobilized, 5% impact
    # Low turnout (<80%): poorly mobilized, 8% impact
    
    def turnout_impact(turnout):
        if pd.isna(turnout):
            return 0.05  # Default to medium
        elif turnout > 90:
            return 0.02  # Already mobilized
        elif turnout > 80:
            return 0.05  # Medium mobilization
        else:
            return 0.08  # Large new voter boost (anti-incumbency)
    
    ac_data["turnout_impact"] = ac_data["turnout_2021"].apply(turnout_impact)
    return ac_data


def _calculate_swing_requirement(calibrated_df):
    """
    Calculate required swing to achieve 5.5% shift.
    
    Exit poll analysis indicates BJP secured 38%, but needs 5.5% swing to 
    "fundamentally alter the outcome" (pass 50% and secure 50%+ seats).
    
    Swing of 5.5% means:
    - BJP gains 5.5% from TMC
    - Distributed across constituencies based on baseline competitiveness
    
    Logic: Close seats (margin 0-10%) respond more to swing than safe seats
    """
    prob_cols = [col for col in calibrated_df.columns if col.startswith("P_")]
    
    # For each seat, calculate "competitiveness"
    # (how close is the race; how responsive to swing)
    tmc_col = "P_All India Trinamool Congress"
    bjp_col = "P_Bharatiya Janta Party"
    
    # Competitiveness: how narrow is the margin?
    calibrated_df["margin_prob"] = abs(
        calibrated_df[tmc_col] - calibrated_df[bjp_col]
    )
    
    # Seats with narrow margins are more swing-sensitive
    # Apply 5.5% swing as direct probability shift
    # But scale it: narrow margins get full impact; wide margins get reduced impact
    swing_sensitivity = 1.0 - (calibrated_df["margin_prob"] / 2.0)  # 0-1 scale
    
    calibrated_df["swing_impact"] = 0.055 * swing_sensitivity
    
    return calibrated_df


def apply_antiinc_and_turnout(calibrated_df, ac_data):
    """
    Apply anti-incumbency and turnout adjustments to calibrated probabilities.
    """
    adjusted = calibrated_df.copy()
    
    # Merge anti-incumbency and turnout factors
    factor_cols = ["AC_Number", "antiinc_squeeze", "turnout_impact"]
    factors = ac_data[factor_cols].copy()
    
    adjusted = adjusted.merge(factors, on="AC_Number", how="left")
    adjusted["antiinc_squeeze"] = adjusted["antiinc_squeeze"].fillna(0.06)
    adjusted["turnout_impact"] = adjusted["turnout_impact"].fillna(0.05)
    
    # Aggregate factors (anti-incumbency + turnout)
    adjusted["combined_factor"] = (
        adjusted["antiinc_squeeze"] + adjusted["turnout_impact"]
    )
    # Cap at 20% (realism constraint)
    adjusted["combined_factor"] = adjusted["combined_factor"].clip(upper=0.20)
    
    # Apply combined adjustment
    tmc_col = "P_All India Trinamool Congress"
    bjp_col = "P_Bharatiya Janta Party"
    other_col = "P_OTHER"
    
    for idx, row in adjusted.iterrows():
        factor = row["combined_factor"]
        tmc_reduction = adjusted.loc[idx, tmc_col] * factor
        
        # 75% of TMC loss goes to BJP (stronger beneficiary)
        # 25% to OTHER (some voters stay home/scatter)
        adjusted.loc[idx, tmc_col] -= tmc_reduction * 0.75
        adjusted.loc[idx, bjp_col] += tmc_reduction * 0.75
        adjusted.loc[idx, other_col] += tmc_reduction * 0.25
    
    # Renormalize
    prob_cols = [tmc_col, bjp_col, other_col]
    total = adjusted[prob_cols].sum(axis=1)
    adjusted[prob_cols] = adjusted[prob_cols].div(total, axis=0)
    
    # Update winner
    adjusted["Predicted_Winner"] = adjusted[prob_cols].idxmax(axis=1).str.replace("P_", "")
    adjusted["Predicted_Winner_Prob"] = adjusted[prob_cols].max(axis=1)
    
    return adjusted


def apply_swing_adjustment(adjusted_df):
    """
    Apply 5.5% swing requirement on top of anti-incumbency/turnout.
    
    This models the scenario where the exit poll requirement of 5.5% swing
    is actually realized on the ground.
    """
    swing_adjusted = adjusted_df.copy()
    
    tmc_col = "P_All India Trinamool Congress"
    bjp_col = "P_Bharatiya Janta Party"
    other_col = "P_OTHER"
    
    # Calculate margin-based sensitivity (tight seats respond more to swing)
    margin_prob = abs(
        swing_adjusted[tmc_col] - swing_adjusted[bjp_col]
    )
    swing_sensitivity = 1.0 - (margin_prob / 2.0)
    swing_impact = 0.055 * swing_sensitivity
    
    for idx, row in swing_adjusted.iterrows():
        impact = swing_impact.iloc[idx]
        
        # TMC loses impact amount as probability
        tmc_loss = swing_adjusted.loc[idx, tmc_col] * impact
        
        # All goes to BJP for swing scenario
        swing_adjusted.loc[idx, tmc_col] -= tmc_loss
        swing_adjusted.loc[idx, bjp_col] += tmc_loss
    
    # Renormalize
    prob_cols = [tmc_col, bjp_col, other_col]
    total = swing_adjusted[prob_cols].sum(axis=1)
    swing_adjusted[prob_cols] = swing_adjusted[prob_cols].div(total, axis=0)
    
    # Update winner
    swing_adjusted["Predicted_Winner"] = swing_adjusted[prob_cols].idxmax(axis=1).str.replace("P_", "")
    swing_adjusted["Predicted_Winner_Prob"] = swing_adjusted[prob_cols].max(axis=1)
    
    return swing_adjusted


def generate_analysis():
    """Generate complete anti-incumbency and turnout analysis"""
    print("Loading calibrated predictions...")
    calibrated = pd.read_csv(CALIBRATED_PATH)
    
    print("Loading 2021 results...")
    ac_2021 = _load_2021_results()
    
    print("Analyzing anti-incumbency factors...")
    ac_2021 = _identify_antiincumbency_vulnerable(ac_2021)
    ac_2021 = _identify_turnout_impact(ac_2021)
    
    # Save analysis
    analysis_cols = [col for col in ["AC_Number", "Constituency_Name", "District", "antiinc_squeeze", "turnout_impact", "Turnout"] if col in ac_2021.columns]
    analysis_output = ac_2021[analysis_cols].copy()
    analysis_output.to_csv(OUTPUT_ANTIINC_PATH, index=False)
    print(f"Anti-incumbency analysis saved: {OUTPUT_ANTIINC_PATH}")
    
    # Apply adjustments
    print("Applying anti-incumbency & turnout adjustments...")
    antiinc_adjusted = apply_antiinc_and_turnout(calibrated, ac_2021)
    
    antiinc_output = antiinc_adjusted[[
        "AC_Number", "Constituency_Name", "District", "Type",
        "Predicted_Winner", "Predicted_Winner_Prob",
        "P_All India Trinamool Congress", "P_Bharatiya Janta Party", "P_OTHER",
        "antiinc_squeeze", "turnout_impact", "combined_factor"
    ]].copy()
    antiinc_output.to_csv(OUTPUT_ANTIINC_PATH, index=False)
    print(f"Anti-incumbency adjusted predictions saved: {OUTPUT_ANTIINC_PATH}")
    
    # Generate tally
    antiinc_tally = (
        antiinc_adjusted["Predicted_Winner"]
        .value_counts()
        .rename_axis("Party")
        .reset_index(name="Seats")
        .sort_values("Seats", ascending=False)
    )
    print(f"\nAnti-Incumbency Adjusted Tally:\n{antiinc_tally}")
    
    # Apply swing adjustment (5.5%)
    print("\nApplying 5.5% swing adjustment...")
    swing_adjusted = apply_swing_adjustment(antiinc_adjusted)
    
    swing_output = swing_adjusted[[
        "AC_Number", "Constituency_Name", "District", "Type",
        "Predicted_Winner", "Predicted_Winner_Prob",
        "P_All India Trinamool Congress", "P_Bharatiya Janta Party", "P_OTHER"
    ]].copy()
    swing_output.to_csv(OUTPUT_SWING_PATH, index=False)
    print(f"Swing-adjusted predictions saved: {OUTPUT_SWING_PATH}")
    
    # Generate tally
    swing_tally = (
        swing_adjusted["Predicted_Winner"]
        .value_counts()
        .rename_axis("Party")
        .reset_index(name="Seats")
        .sort_values("Seats", ascending=False)
    )
    print(f"\n5.5% Swing Adjusted Tally:\n{swing_tally}")
    
    # Combined scenario: All factors (margin squeeze + anti-incumbency + swing)
    print("\nLoading margin squeeze adjusted predictions...")
    margin_squeezed = pd.read_csv(ADJUSTED_SQUEEZE_PATH)
    
    print("Combining all factors (margin squeeze + anti-incumbency + turnout + swing)...")
    combined = margin_squeezed.copy()
    
    # Merge additional factors
    factor_cols = ["AC_Number", "antiinc_squeeze", "turnout_impact"]
    factors = ac_2021[factor_cols].copy()
    combined = combined.merge(factors, on="AC_Number", how="left")
    combined["antiinc_squeeze"] = combined["antiinc_squeeze"].fillna(0.06)
    combined["turnout_impact"] = combined["turnout_impact"].fillna(0.05)
    
    # Add combined squeeze factor
    if "squeeze_pct" in combined.columns:
        combined["total_all_factors"] = (
            combined["squeeze_pct"] + 
            combined["antiinc_squeeze"] + 
            combined["turnout_impact"]
        )
    else:
        combined["total_all_factors"] = (
            combined["antiinc_squeeze"] + 
            combined["turnout_impact"]
        )
    
    combined["total_all_factors"] = combined["total_all_factors"].clip(upper=0.35)
    
    # Apply combined adjustment
    tmc_col = "P_All India Trinamool Congress"
    bjp_col = "P_Bharatiya Janta Party"
    other_col = "P_OTHER"
    
    for idx, row in combined.iterrows():
        factor = row["total_all_factors"]
        tmc_reduction = combined.loc[idx, tmc_col] * factor
        
        # 75% to BJP, 25% to OTHER
        combined.loc[idx, tmc_col] -= tmc_reduction * 0.75
        combined.loc[idx, bjp_col] += tmc_reduction * 0.75
        combined.loc[idx, other_col] += tmc_reduction * 0.25
    
    # Renormalize
    prob_cols = [tmc_col, bjp_col, other_col]
    total = combined[prob_cols].sum(axis=1)
    combined[prob_cols] = combined[prob_cols].div(total, axis=0)
    
    combined["Predicted_Winner"] = combined[prob_cols].idxmax(axis=1).str.replace("P_", "")
    combined["Predicted_Winner_Prob"] = combined[prob_cols].max(axis=1)
    
    combined_output = combined[[
        "AC_Number", "Constituency_Name", "District", "Type",
        "Predicted_Winner", "Predicted_Winner_Prob",
        "P_All India Trinamool Congress", "P_Bharatiya Janta Party", "P_OTHER",
        "total_all_factors"
    ]].copy()
    combined_output.to_csv(OUTPUT_COMBINED_PATH, index=False)
    print(f"Combined factors predictions saved: {OUTPUT_COMBINED_PATH}")
    
    # Generate tally
    combined_tally = (
        combined["Predicted_Winner"]
        .value_counts()
        .rename_axis("Party")
        .reset_index(name="Seats")
        .sort_values("Seats", ascending=False)
    )
    combined_tally.to_csv(OUTPUT_COMBINED_TALLY, index=False)
    print(f"\nCombined All-Factors Tally:\n{combined_tally}")
    
    return {
        "baseline": pd.read_csv(CALIBRATED_PATH),
        "margin_squeeze": margin_squeezed,
        "antiinc": antiinc_adjusted,
        "swing": swing_adjusted,
        "combined": combined,
    }


if __name__ == "__main__":
    results = generate_analysis()
