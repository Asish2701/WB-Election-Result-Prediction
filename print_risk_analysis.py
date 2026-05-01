import pandas as pd

# Load squeeze analysis and calibrated predictions
squeeze = pd.read_csv('outputs/wb_2026_margin_squeeze_analysis.csv')
calibrated = pd.read_csv('outputs/wb_2026_calibrated.csv')
adjusted = pd.read_csv('outputs/wb_2026_adjusted_for_squeeze.csv')

# Merge to get winner predictions
risk_df = pd.merge(
    squeeze[['AC_Number', 'Constituency_Name', 'District', 'Margin_Pct', 'total_squeeze_pct']],
    calibrated[['AC_Number', 'Predicted_Winner', 'Predicted_Winner_Prob']],
    on='AC_Number',
    suffixes=('', '_baseline')
)

risk_df = pd.merge(
    risk_df,
    adjusted[['AC_Number', 'Predicted_Winner', 'Predicted_Winner_Prob']],
    on='AC_Number',
    suffixes=('_baseline', '_adjusted')
)

# Get top 30 by squeeze factor
top_30 = risk_df.nlargest(30, 'total_squeeze_pct')

# Show constituencies where TMC is predicted to win but at risk
tmc_at_risk = top_30[top_30['Predicted_Winner_baseline'] == 'All India Trinamool Congress'].copy()
tmc_at_risk = tmc_at_risk.sort_values('total_squeeze_pct', ascending=False)

print("=" * 140)
print("TOP 20 TMC-HELD CONSTITUENCIES AT RISK FROM MARGIN SQUEEZE")
print("=" * 140)
print(tmc_at_risk[['AC_Number', 'Constituency_Name', 'District', 'Margin_Pct', 'total_squeeze_pct', 'Predicted_Winner_Prob_baseline', 'Predicted_Winner_Prob_adjusted']].head(20).to_string(index=False))

print("\n\n")
print("=" * 140)
print("SEATS FLIPPING FROM TMC TO BJP UNDER MARGIN SQUEEZE")
print("=" * 140)
flips = top_30[top_30['Predicted_Winner_baseline'] != top_30['Predicted_Winner_adjusted']]
print(flips[['AC_Number', 'Constituency_Name', 'District', 'Predicted_Winner_baseline', 'Predicted_Winner_adjusted', 'Predicted_Winner_Prob_adjusted']].to_string(index=False))

# Save a comprehensive risk report
risk_report = risk_df.sort_values('total_squeeze_pct', ascending=False)
risk_report.to_csv('outputs/wb_2026_comprehensive_risk_report.csv', index=False)
print(f"\n\nComprehensive risk report saved to: outputs/wb_2026_comprehensive_risk_report.csv")
