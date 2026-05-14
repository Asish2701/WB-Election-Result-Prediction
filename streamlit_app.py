import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Model Accuracy Dashboard", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700&family=Sora:wght@500;700&display=swap');

    :root {
        --ink: #101827;
        --muted: #5b6475;
        --bg: #f6f8fb;
        --card: #4099ff;
        --accent: #0f766e;
        --danger: #b91c1c;
        --border: #dbe2ea;
    }

    .stApp {
        background:
            radial-gradient(900px 400px at 8% -5%, #e8f5ff 0%, rgba(232, 245, 255, 0) 58%),
            radial-gradient(800px 400px at 100% 0%, #ecfdf5 0%, rgba(236, 253, 245, 0) 60%),
            var(--bg);
        color: var(--ink);
        font-family: 'Outfit', sans-serif;
    }

    h1, h2, h3, h4 {
        font-family: 'Sora', sans-serif;
        letter-spacing: -0.2px;
    }

    .hero {
        background: linear-gradient(120deg, #0f766e, #0e7490);
        color: #ffffff;
        border-radius: 16px;
        padding: 1rem 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 10px 26px rgba(14, 116, 144, 0.2);
    }

    .hero p {
        margin: 0;
        opacity: 0.95;
    }

    div[data-testid="stMetric"] {
        border: 1px solid var(--border);
        border-radius: 12px;
        background: var(--card);
        padding: 0.35rem 0.5rem;
    }

    div[data-testid="stMetricLabel"] {
        color: #1e293b;
        opacity: 1;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        color: #0f172a;
        font-weight: 700;
    }

    div[data-testid="stMetricDelta"] {
        color: #166534;
    }

    /* Some Streamlit builds render labels through nested paragraph tags */
    div[data-testid="stMetricLabel"] p {
        color: #1e293b !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }

    div[data-testid="stMetricValue"] p {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetricDelta"] p {
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

METRICS_PATH = Path("outputs/training_metrics.json")
ACTUAL_VS_PREDICTED_PATH = Path("outputs/wb_2026_actual_vs_predicted.csv")
CONSTITUENCY_COMP_PATH = Path("outputs/wb_2026_constituency_comparison.csv")


@st.cache_data
def load_training_metrics():
    if not METRICS_PATH.exists():
        return {}
    try:
        return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


@st.cache_data
def load_csv(path: Path):
    if not path.exists():
        return None
    return pd.read_csv(path)


def build_confidence_bins(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work = work.dropna(subset=["Predicted_Winner_Prob"])
    if work.empty:
        return pd.DataFrame()

    bins = [0.0, 0.6, 0.75, 0.85, 0.95, 1.0]
    labels = ["0-60%", "60-75%", "75-85%", "85-95%", "95-100%"]
    work["confidence_band"] = pd.cut(
        work["Predicted_Winner_Prob"],
        bins=bins,
        labels=labels,
        include_lowest=True,
    )

    band = (
        work.groupby("confidence_band", observed=False)
        .agg(
            predictions=("Correct_Prediction", "size"),
            accuracy=("Correct_Prediction", "mean"),
        )
        .reset_index()
    )
    band["accuracy_pct"] = (band["accuracy"] * 100).round(1)
    return band


def safe_column(df: pd.DataFrame, col: str, fallback: str):
    return col if col in df.columns else fallback


def unique_columns(columns):
    seen = set()
    ordered = []
    for col in columns:
        if col and col not in seen:
            ordered.append(col)
            seen.add(col)
    return ordered


training_metrics = load_training_metrics()
actual_vs_pred = load_csv(ACTUAL_VS_PREDICTED_PATH)
constituency_comp = load_csv(CONSTITUENCY_COMP_PATH)

st.markdown(
    """
    <div class="hero">
        <h2>Model Accuracy and Lag Dashboard</h2>
        <p>Clean view of what worked, where it failed, and where the biggest gaps are.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

<<<<<<< HEAD
if constituency_comp is None and actual_vs_pred is None:
    st.error(
        "Missing comparison files in outputs/. Expected wb_2026_constituency_comparison.csv "
        "and/or wb_2026_actual_vs_predicted.csv"
=======
# Create tabs for different analyses
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview", 
    " Margin Squeeze", 
    " Anti-Incumbency",
    " Scenarios",
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
        sorted(df_display[winner_col].dropna().unique()),
        default=sorted(df_display[winner_col].dropna().unique()),
>>>>>>> b28b9c0eb9e9fc9095e1d3e86ec8f51a74feb81a
    )
    st.stop()

col1, col2, col3, col4 = st.columns(4)

train_accuracy = float(training_metrics.get("accuracy", 0.0)) * 100
f1_macro = float(training_metrics.get("f1_macro", 0.0)) * 100

if constituency_comp is not None and "Correct_Prediction" in constituency_comp.columns:
    overall_accuracy = constituency_comp["Correct_Prediction"].mean() * 100
else:
    overall_accuracy = train_accuracy

if constituency_comp is not None and "Predicted_Winner_Prob" in constituency_comp.columns:
    incorrect = constituency_comp[constituency_comp["Correct_Prediction"] == False].copy()
    high_conf_wrong = incorrect[incorrect["Predicted_Winner_Prob"] >= 0.85]
    high_conf_wrong_pct = (len(high_conf_wrong) / max(len(constituency_comp), 1)) * 100
else:
    high_conf_wrong = pd.DataFrame()
    high_conf_wrong_pct = 0.0

largest_party_gap = 0
if actual_vs_pred is not None and "Difference" in actual_vs_pred.columns:
    numeric_diff = pd.to_numeric(actual_vs_pred["Difference"], errors="coerce").fillna(0)
    largest_party_gap = int(numeric_diff.abs().max())

col1.metric("Overall Accuracy", f"{overall_accuracy:.1f}%")
col2.metric("Train Accuracy", f"{train_accuracy:.1f}%")
col3.metric("Macro F1", f"{f1_macro:.1f}%")
col4.metric(
    "High-Confidence Misses",
    f"{high_conf_wrong_pct:.1f}%",
    f"{len(high_conf_wrong)} seats",
    delta_color="inverse",
)

st.divider()

left, right = st.columns([1.2, 1])

with left:
    st.subheader("Party-Level Gap: Predicted vs Actual")
    if actual_vs_pred is not None:
        comp = actual_vs_pred.copy()
        comp = comp[pd.to_numeric(comp["Actual_Seats"], errors="coerce").notna()].copy()
        comp = comp[comp["Party"] != "Total"] if "Party" in comp.columns else comp

        plot_df = comp.melt(
            id_vars=["Party"],
            value_vars=["Predicted_Seats", "Actual_Seats"],
            var_name="Series",
            value_name="Seats",
        )
        fig_gap = px.bar(
            plot_df,
            x="Party",
            y="Seats",
            color="Series",
            barmode="group",
            color_discrete_map={"Predicted_Seats": "#0e7490", "Actual_Seats": "#b91c1c"},
        )
        fig_gap.update_layout(height=420, legend_title_text="")
        st.plotly_chart(fig_gap, use_container_width=True)

        st.caption(f"Largest party-level seat gap: {largest_party_gap} seats")
    else:
        st.info("No party-level comparison file found.")

with right:
    st.subheader("Where the Model Lags Most")
    if constituency_comp is not None and "Prediction_Error" in constituency_comp.columns:
        lag_pairs = (
            constituency_comp[constituency_comp["Correct_Prediction"] == False]["Prediction_Error"]
            .value_counts()
            .reset_index()
        )
        lag_pairs.columns = ["Prediction Error Pattern", "Count"]
        lag_pairs = lag_pairs.head(8)

        fig_lag = px.bar(
            lag_pairs,
            x="Count",
            y="Prediction Error Pattern",
            orientation="h",
            color="Count",
            color_continuous_scale="Reds",
        )
        fig_lag.update_layout(height=420, yaxis_title="", coloraxis_showscale=False)
        st.plotly_chart(fig_lag, use_container_width=True)
    else:
        st.info("No constituency-level error patterns available.")

st.divider()

if constituency_comp is not None and "Predicted_Winner_Prob" in constituency_comp.columns:
    st.subheader("Confidence vs Accuracy")
    band = build_confidence_bins(constituency_comp)
    if not band.empty:
        fig_band = px.line(
            band,
            x="confidence_band",
            y="accuracy_pct",
            markers=True,
        )
        fig_band.update_traces(line_color="#0f766e", marker_size=9)
        fig_band.update_layout(height=320, yaxis_title="Accuracy (%)", xaxis_title="Confidence Band")
        st.plotly_chart(fig_band, use_container_width=True)

st.divider()

if constituency_comp is not None:
    st.subheader("Top High-Confidence Wrong Predictions")
    required_cols = ["Correct_Prediction", "Predicted_Winner_Prob", "Predicted_Winner", "Actual_Party"]
    if all(col in constituency_comp.columns for col in required_cols):
        incorrect = constituency_comp[constituency_comp["Correct_Prediction"] == False].copy()
        incorrect = incorrect.sort_values("Predicted_Winner_Prob", ascending=False).head(20)

        ac_col = "AC_Number" if "AC_Number" in incorrect.columns else None
        name_col = "Constituency_Name" if "Constituency_Name" in incorrect.columns else None
        display_cols = [
            ac_col,
            name_col,
            "Predicted_Winner",
            "Actual_Party",
            "Predicted_Winner_Prob",
            "Prediction_Error",
        ]
        display_cols = [col for col in display_cols if col in incorrect.columns]
        display_cols = unique_columns(display_cols)

        table = incorrect[display_cols].rename(
            columns={
                "Predicted_Winner_Prob": "Confidence",
                "Predicted_Winner": "Predicted",
                "Actual_Party": "Actual",
            }
        )
        table = table.loc[:, ~table.columns.duplicated()]

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            height=420,
        )
    else:
        st.info("Comparison data does not include enough columns to show lag points.")

st.caption(
    "Scope kept intentionally narrow: accuracy, major misses, and confidence failures. "
    "Removed scenario clutter and narrative-heavy sections for a clean performance view."
)
