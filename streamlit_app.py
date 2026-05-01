import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="WB 2026 Election Dashboard", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Space+Grotesk:wght@400;600&display=swap');

    :root {
        --bg-1: #0f0f12;
        --bg-2: #1b1b26;
        --accent: #e53935;
        --accent-2: #f2c94c;
        --text: #f7f7f7;
        --muted: #c9c9d4;
        --card: #171720;
    }

    .stApp {
        background: radial-gradient(1200px 600px at 15% 10%, #23233a 0%, rgba(35,35,58,0) 60%),
                    radial-gradient(900px 500px at 85% 20%, #2a1b1b 0%, rgba(42,27,27,0) 55%),
                    linear-gradient(160deg, var(--bg-1), var(--bg-2));
        color: var(--text);
        font-family: 'Space Grotesk', sans-serif;
    }

    h1, h2, h3, h4, h5 {
        font-family: 'Rajdhani', sans-serif;
        letter-spacing: 0.5px;
    }

    .header-wrap {
        padding: 0.5rem 0 0.5rem 0;
        animation: fadein 0.8s ease-in;
    }

    .kpi-card {
        background: var(--card);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.35);
    }

    @keyframes fadein {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_PATH = Path("outputs/wb_2026_powerbi_dataset.csv")
FLIP_PATH = Path("outputs/wb_2026_flip_risk.csv")
EXIT_POLL_PATH = Path("outputs/wb_2026_exit_polls.csv")
MARGIN_SQUEEZE_PATH = Path("outputs/wb_2026_margin_squeeze_analysis.csv")
ADJUSTED_SQUEEZE_PATH = Path("outputs/wb_2026_adjusted_for_squeeze.csv")
ANTIINC_PATH = Path("outputs/wb_2026_antiincumbency_analysis.csv")
COMBINED_PATH = Path("outputs/wb_2026_all_factors_combined.csv")


@st.cache_data
def load_data():
    if not DATA_PATH.exists():
        return None, None, None, None, None, None, None
    df = pd.read_csv(DATA_PATH)
    flip = pd.read_csv(FLIP_PATH) if FLIP_PATH.exists() else None
    exit_polls = pd.read_csv(EXIT_POLL_PATH) if EXIT_POLL_PATH.exists() else None
    margin_squeeze = pd.read_csv(MARGIN_SQUEEZE_PATH) if MARGIN_SQUEEZE_PATH.exists() else None
    adjusted_squeeze = pd.read_csv(ADJUSTED_SQUEEZE_PATH) if ADJUSTED_SQUEEZE_PATH.exists() else None
    antiinc = pd.read_csv(ANTIINC_PATH) if ANTIINC_PATH.exists() else None
    combined = pd.read_csv(COMBINED_PATH) if COMBINED_PATH.exists() else None
    return df, flip, exit_polls, margin_squeeze, adjusted_squeeze, antiinc, combined


def pick_prob_cols(df):
    for suffix in ["_calibrated", "_baseline", ""]:
        cols = [col for col in df.columns if col.startswith("P_") and col.endswith(suffix)]
        if cols:
            return cols
    return []


def get_winner_columns(df):
    # Check for various column name patterns
    if "Predicted_Winner" in df.columns:
        return "Predicted_Winner", "Predicted_Winner_Prob"
    elif "Predicted_Winner_baseline" in df.columns:
        return "Predicted_Winner_baseline", "Predicted_Winner_Prob_baseline"
    elif "Predicted_Winner_adjusted" in df.columns:
        return "Predicted_Winner_adjusted", "Predicted_Winner_Prob_adjusted"
    else:
        # Fallback to first matching columns
        for col in df.columns:
            if "Predicted_Winner" in col:
                prob_col = col.replace("Predicted_Winner", "Predicted_Winner_Prob")
                if prob_col in df.columns:
                    return col, prob_col
        return "Predicted_Winner_baseline", "Predicted_Winner_Prob_baseline"


def build_grid(df, risk_col, winner_col, winner_prob_col):
    grid_cols = 14
    df = df.copy()
    df["grid_x"] = (df["AC_Number"] - 1) % grid_cols
    df["grid_y"] = (df["AC_Number"] - 1) // grid_cols
    color_map = {
        "Very High": "#ff5c57",
        "High": "#ff9f1c",
        "Medium": "#ffd166",
        "Low": "#8ac926",
        "Very Low": "#1982c4",
    }
    fig = px.scatter(
        df,
        x="grid_x",
        y="grid_y",
        color=risk_col,
        color_discrete_map=color_map,
        hover_data={
            "AC_Number": True,
            "Constituency_Name": True,
            winner_col: True,
            winner_prob_col: ":.2f",
            "grid_x": False,
            "grid_y": False,
        },
    )
    fig.update_traces(marker=dict(size=14, symbol="square"))
    fig.update_layout(
        height=520,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="Flip Risk",
    )
    fig.update_yaxes(autorange="reversed")
    return fig


df, flip, exit_polls, margin_squeeze, adjusted_squeeze, antiinc, combined = load_data()

if df is None:
    st.error("Missing outputs/wb_2026_powerbi_dataset.csv. Generate it first.")
    st.stop()

# Use combined scenario if available, otherwise fall back to baseline
df_display = combined if combined is not None else df

winner_col, winner_prob_col = get_winner_columns(df_display)

if flip is not None:
    df_display = df_display.merge(flip[["AC_Number", "Flip_Risk"]], on="AC_Number", how="left")
else:
    df_display["Flip_Risk"] = "Medium"

prob_cols = pick_prob_cols(df_display)

st.markdown(
    """
    <div class="header-wrap">
        <h1>West Bengal 2026 Election Dashboard</h1>
        <p style="color:#c9c9d4; margin-top:-10px;">Comprehensive analysis: baseline predictions, margin squeeze, anti-incumbency, and scenario modeling.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Create tabs for different analyses
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    "💪 Margin Squeeze", 
    "⚖️ Anti-Incumbency",
    "🎯 Scenarios",
    "🔍 Details"
])

with tab1:
    # Determine which scenario we're showing
    is_combined = combined is not None
    scenario_title = "Comprehensive Scenario" if is_combined else "Baseline Predictions"
    scenario_subtitle = "All factors combined (margin squeeze + anti-incumbency + turnout + swing)" if is_combined else "Baseline model without scenario adjustments"
    
    st.subheader(scenario_title)
    st.caption(scenario_subtitle)
    
    col_a, col_b, col_c, col_d = st.columns(4)
    
    party_counts = df_display[winner_col].value_counts()
    col_a.metric("AITC Seats", int(party_counts.get("All India Trinamool Congress", 0)))
    col_b.metric("BJP Seats", int(party_counts.get("Bharatiya Janta Party", 0)))
    col_c.metric("Other Seats", int(party_counts.get("OTHER", 0)))
    col_d.metric("Median Win Prob", f"{df_display[winner_prob_col].median():.2f}")

    st.divider()

    # Show scenario comparison if combined data is available
    if is_combined:
        st.subheader("Scenario Progression")
        scenario_comparison = pd.DataFrame({
            'Scenario': ['Baseline', 'Margin Squeeze', 'Margin Squeeze\n+ Anti-Inc', 'All Factors\nCombined'],
            'TMC Seats': [197, 194, '188-190', int(party_counts.get("All India Trinamool Congress", 0))],
            'BJP Seats': [95, 98, '102-104', int(party_counts.get("Bharatiya Janta Party", 0))]
        })
        st.dataframe(scenario_comparison, use_container_width=True, hide_index=True)
        st.divider()

    left, right = st.columns([2.2, 1.2])

    with left:
        st.subheader("Seat Grid Map (Flip Risk)")
        st.plotly_chart(build_grid(df_display, "Flip_Risk", winner_col, winner_prob_col), use_container_width=True)

    with right:
        st.subheader("Exit Polls vs Model")
        if exit_polls is not None:
            model_row = pd.DataFrame(
                [
                    {
                        "Pollster": "Model (Combined)",
                        "BJP": int(party_counts.get("Bharatiya Janta Party", 0)),
                        "TMC": int(party_counts.get("All India Trinamool Congress", 0)),
                        "Others": int(party_counts.get("OTHER", 0)),
                    }
                ]
            )
            poll_df = pd.concat([exit_polls, model_row], ignore_index=True)
            poll_long = poll_df.melt(id_vars="Pollster", var_name="Party", value_name="Seats")
            fig_poll = px.bar(
                poll_long,
                x="Pollster",
                y="Seats",
                color="Party",
                barmode="group",
                color_discrete_map={
                    "BJP": "#f97316",
                    "TMC": "#e11d48",
                    "Others": "#94a3b8",
                },
            )
            fig_poll.update_layout(height=420, legend_title_text="")
            st.plotly_chart(fig_poll, use_container_width=True)
        else:
            st.info("Exit poll file missing. Add outputs/wb_2026_exit_polls.csv")

    st.subheader("Seat Table")

    party_filter = st.multiselect(
        "Filter by party",
        sorted(df[winner_col].dropna().unique()),
        default=sorted(df[winner_col].dropna().unique()),
    )

    risk_filter = st.multiselect(
        "Filter by flip risk",
        ["Very High", "High", "Medium", "Low", "Very Low"],
        default=["Very High", "High", "Medium", "Low", "Very Low"],
    )

    prob_range = st.slider("Win probability range", 0.0, 1.0, (0.4, 1.0), 0.01)

    filtered = df_display[
        (df_display[winner_col].isin(party_filter))
        & (df_display["Flip_Risk"].isin(risk_filter))
        & (df_display[winner_prob_col].between(prob_range[0], prob_range[1]))
    ].copy()

    candidate_cols = [col for col in df.columns if col.startswith("Candidate_")]

    columns = [
        "AC_Number",
        "Constituency_Name",
        "District",
        "Type",
        winner_col,
        winner_prob_col,
        "Flip_Risk",
    ]

    for col in sorted(candidate_cols):
        if col in df.columns:
            columns.append(col)

    st.dataframe(filtered[columns], use_container_width=True, height=420)

    st.subheader("Win Probability Distribution")
    fig_hist = px.histogram(
        df_display,
        x=winner_prob_col,
        nbins=20,
        color=winner_col,
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    fig_hist.update_layout(height=320, legend_title_text="")
    st.plotly_chart(fig_hist, use_container_width=True)

with tab2:
    st.subheader("Margin Squeeze Analysis")
    
    if margin_squeeze is not None:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Purge Squeeze", f"{margin_squeeze['purge_squeeze'].mean():.1%}")
        col2.metric("Avg RG Kar Squeeze", f"{margin_squeeze['rgkar_squeeze'].mean():.1%}")
        col3.metric("Avg Corruption Squeeze", f"{margin_squeeze['corruption_squeeze'].mean():.1%}")
        col4.metric("Avg Sandeshkhali Squeeze", f"{margin_squeeze['sandeshkhali_squeeze'].mean():.1%}")
        
        st.divider()
        
        # Top constituencies at risk
        st.subheader("Top 20 Constituencies at Risk (by Total Squeeze %)")
        top_squeeze = margin_squeeze.nlargest(20, 'total_squeeze_pct')[
            ['AC_Number', 'Constituency_Name', 'District', 'Margin_Pct', 'total_squeeze_pct', 
             'purge_squeeze', 'rgkar_squeeze', 'corruption_squeeze', 'sandeshkhali_squeeze']
        ].copy()
        top_squeeze.columns = ['AC', 'Constituency', 'District', 'Margin %', 'Total Squeeze %', 
                               'Purge', 'RG Kar', 'Corruption', 'Sandeshkhali']
        st.dataframe(top_squeeze, use_container_width=True)
        
        # Visualization: squeeze factors by district
        st.subheader("Average Squeeze Factors by District")
        district_squeeze = margin_squeeze.groupby('District')[
            ['purge_squeeze', 'rgkar_squeeze', 'corruption_squeeze', 'sandeshkhali_squeeze']
        ].mean().reset_index()
        district_squeeze = district_squeeze.sort_values('purge_squeeze', ascending=False).head(10)
        
        fig_district = px.bar(
            district_squeeze.melt(id_vars='District', var_name='Factor', value_name='Value'),
            x='District',
            y='Value',
            color='Factor',
            barmode='stack',
            color_discrete_map={
                'purge_squeeze': '#ff5c57',
                'rgkar_squeeze': '#ff9f1c',
                'corruption_squeeze': '#ffd166',
                'sandeshkhali_squeeze': '#8ac926'
            },
            title="Margin Squeeze Factors by District"
        )
        fig_district.update_layout(height=400)
        st.plotly_chart(fig_district, use_container_width=True)
        
        # Comparison: baseline vs adjusted
        if adjusted_squeeze is not None:
            st.subheader("Baseline vs Squeeze-Adjusted Predictions")
            baseline_tmc = len(df[df[winner_col] == "All India Trinamool Congress"])
            adjusted_tmc = len(adjusted_squeeze[adjusted_squeeze['Predicted_Winner'] == "All India Trinamool Congress"])
            
            baseline_bjp = len(df[df[winner_col] == "Bharatiya Janta Party"])
            adjusted_bjp = len(adjusted_squeeze[adjusted_squeeze['Predicted_Winner'] == "Bharatiya Janta Party"])
            
            comparison_data = pd.DataFrame({
                'Scenario': ['Baseline', 'After Margin Squeeze'],
                'TMC': [baseline_tmc, adjusted_tmc],
                'BJP': [baseline_bjp, adjusted_bjp],
                'Others': [294 - baseline_tmc - baseline_bjp, 294 - adjusted_tmc - adjusted_bjp]
            })
            
            fig_comparison = px.bar(
                comparison_data.melt(id_vars='Scenario', var_name='Party', value_name='Seats'),
                x='Scenario',
                y='Seats',
                color='Party',
                barmode='group',
                color_discrete_map={'TMC': '#e11d48', 'BJP': '#f97316', 'Others': '#94a3b8'},
                title="Seat Projections: Baseline vs Margin Squeeze"
            )
            fig_comparison.update_layout(height=400)
            st.plotly_chart(fig_comparison, use_container_width=True)
    else:
        st.info("Margin squeeze analysis not available. Run margin_squeeze_analysis.py first.")

with tab3:
    st.subheader("Anti-Incumbency Analysis")
    
    st.markdown("""
    ### Impact of 15 Years of TMC Rule
    
    Anti-incumbency sentiment is rising due to:
    - **Governance concerns**: Corruption, "cut money" culture
    - **RG Kar Medical Case**: Women voter disillusionment
    - **Voter fatigue**: 15 years of same party rule
    - **Business mobility**: Industry concerns about favorable investment climate
    """)
    
    # District-level anti-incumbency impact
    st.subheader("Anti-Incumbency by District")
    
    antiinc_map = {
        "Kolkata": 0.12,
        "North Twenty Four Parganas": 0.10,
        "Haora": 0.10,
        "Hugli": 0.08,
        "Barddhaman": 0.09,
        "Maldah": 0.08,
        "Murshidabad": 0.07,
        "Nadia": 0.06,
    }
    
    antiinc_df = pd.DataFrame(list(antiinc_map.items()), columns=['District', 'Anti-Incumbency Factor'])
    antiinc_df = antiinc_df.sort_values('Anti-Incumbency Factor', ascending=False)
    
    fig_antiinc = px.bar(
        antiinc_df,
        x='District',
        y='Anti-Incumbency Factor',
        title="Anti-Incumbency Impact by District (% Margin Squeeze)",
        color='Anti-Incumbency Factor',
        color_continuous_scale='Reds'
    )
    fig_antiinc.update_layout(height=400)
    st.plotly_chart(fig_antiinc, use_container_width=True)
    
    # Turnout impact
    st.subheader("Record Turnout Effect (91.5% in some phases)")
    
    turnout_df = pd.DataFrame({
        'Turnout Range': ['<80%', '80-90%', '>90%'],
        'New Voter Impact': ['8% squeeze', '5% squeeze', '2% squeeze'],
        'Interpretation': [
            'Strong anti-incumbency signal (massive new voter mobilization)',
            'Moderate anti-incumbency signal',
            'Election as normal (baseline expectations)'
        ]
    })
    st.dataframe(turnout_df, use_container_width=True)
    
    st.info("Record 91.5% turnout in recent phases signals strong 'change wave' - new voters mobilizing for opposition.")

with tab4:
    st.subheader("Comprehensive Scenario Analysis")
    
    st.markdown("""
    ### Four Scenarios: TMC's Path to Victory
    
    Based on combination of margin squeeze, anti-incumbency, turnout effects, and 5.5% swing requirement from exit polls.
    """)
    
    scenarios = pd.DataFrame({
        'Scenario': [
            'Baseline (No Factors)',
            'Margin Squeeze Only',
            'Margin Squeeze + Anti-Incumbency',
            'Full Wave (All Factors + 5.5% Swing)'
        ],
        'TMC Seats': [197, 194, '188-190', '177-182'],
        'BJP Seats': [95, 98, '102-104', '110-115'],
        'TMC Majority': ['+22', '+19', '+13-15', '+2-7'],
        'Probability': ['0%', '40%', '35%', '5%']
    })
    
    st.dataframe(scenarios, use_container_width=True)
    
    st.divider()
    
    st.subheader("Exit Poll Signal: 5.5% Swing Requirement")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("BJP Exit Poll Target", "43%+ vote share")
        st.metric("Current Model", "38% vote share")
    with col2:
        st.metric("Gap to Close", "5.5%")
        st.metric("Swing Impact", "10-15 additional seats")
    
    st.divider()
    
    st.subheader("Scenario Probability Assessment")
    scenario_data = pd.DataFrame({
        'Scenario': [
            'Margin Squeeze Only',
            'Margin Squeeze +\nAnti-Incumbency',
            'Anti-Incumbency +\nTurnout Effect',
            'Full Change Wave'
        ],
        'Probability': [40, 35, 15, 5],
        'TMC Seats (Mid)': [194, 189, 185, 180]
    })
    
    fig_scenarios = go.Figure()
    
    fig_scenarios.add_trace(go.Bar(
        x=scenario_data['Scenario'],
        y=scenario_data['Probability'],
        name='Probability',
        marker=dict(color=['#3b82f6', '#8b5cf6', '#ec4899', '#f97316']),
        yaxis='y1'
    ))
    
    fig_scenarios.add_trace(go.Scatter(
        x=scenario_data['Scenario'],
        y=scenario_data['TMC Seats (Mid)'],
        name='TMC Seats (Midpoint)',
        marker=dict(color='#e11d48', size=10),
        yaxis='y2'
    ))
    
    fig_scenarios.update_layout(
        title="Scenario Probabilities and Seat Outcomes",
        xaxis_title="Scenario",
        yaxis=dict(title="Probability (%)", side='left'),
        yaxis2=dict(title="TMC Seats", side='right', overlaying='y'),
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_scenarios, use_container_width=True)

with tab5:
    st.subheader("Critical Constituencies & Detailed View")
    
    # Vulnerability clusters
    st.subheader("🔴 Top Vulnerability Clusters")
    
    clusters = {
        'Murshidabad (9 seats)': {
            'Factors': 'Voter purge (35%) + anti-incumbency (7%)',
            'Risk': 'VERY HIGH',
            'At Risk': 'Suti, Raninagar, Sagardighi, Lalgola, Beldanga',
            'Signal': 'Early trends in Murshidabad will be bellwether for entire state'
        },
        'Maldah (5 seats)': {
            'Factors': 'Voter purge (30%) + corruption narrative (12%)',
            'Risk': 'VERY HIGH',
            'At Risk': 'Ratua, Baisnabnagar, Mothabari',
            'Signal': 'Judicial gherao incident narrative resonance'
        },
        'North 24 Parganas (14 seats)': {
            'Factors': 'RG Kar (10%) + Sandeshkhali (8%) + anti-incumbency (10%)',
            'Risk': 'VERY HIGH',
            'At Risk': 'Panihati, Sandeshkhali, Basirhat',
            'Signal': 'Women voter behavior, freed voter movement'
        },
        'Barddhaman (19 seats)': {
            'Factors': 'Corruption narrative (8%) + industrial concerns (9%)',
            'Risk': 'HIGH',
            'At Risk': 'Burdwan Dakshin, Burwan, Asansol',
            'Signal': 'Industrial worker sentiment'
        }
    }
    
    for cluster_name, details in clusters.items():
        with st.expander(f"**{cluster_name}** - {details['Risk']} Risk"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Factors**: {details['Factors']}")
                st.write(f"**At Risk**: {details['At Risk']}")
            with col2:
                st.write(f"**Signal**: {details['Signal']}")
    
    st.divider()
    
    st.subheader("Election Night Monitoring Checklist")
    
    st.markdown("""
    #### Phase 1: Early Exits (by 6 PM)
    Monitor these districts for exit poll validation:
    1. **Murshidabad** - Target: TMC 50%+ | If <45%: Anti-incumbency wave confirmed
    2. **Maldah** - Target: TMC 45%+ | If <40%: Purge + corruption narrative working
    3. **Kolkata** - Target: TMC 55%+ | If <50%: Urban voter shift confirmed
    
    #### Phase 2: Early Counts (10 PM onwards)
    Watch flip risk in:
    - Burdwan Dakshin (AC 260)
    - Burwan (AC 67)
    - Panskura Paschim
    - Panihati (AC 111)
    - Sandeshkhali (AC 123)
    
    #### Phase 3: Trend Confirmation (By Midnight)
    - If TMC leading in <160 seats at 50% count: **LOSS likely**
    - If TMC leading in 160-175 seats: **Close call**
    - If TMC leading in >175 seats: **Majority secure**
    """)
    
    st.divider()
    
    st.subheader("Data Downloads")
    
    if margin_squeeze is not None:
        csv = margin_squeeze.to_csv(index=False)
        st.download_button(
            label="Download Margin Squeeze Analysis",
            data=csv,
            file_name="wb_2026_margin_squeeze_analysis.csv",
            mime="text/csv"
        )
    
    if adjusted_squeeze is not None:
        csv = adjusted_squeeze.to_csv(index=False)
        st.download_button(
            label="Download Squeeze-Adjusted Predictions",
            data=csv,
            file_name="wb_2026_adjusted_for_squeeze.csv",
            mime="text/csv"
        )
