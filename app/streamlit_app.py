from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.dashboard_components import department_comparison, forecast_chart, kpi_card, occupancy_trend, resource_heatmap, wait_time_chart
from src.config import CLEAN_PATIENTS, DAILY_DEPARTMENT, FORECAST_OUTPUT, RECOMMENDATIONS_OUTPUT
from src.optimization import simulate_icu_bed_increase


st.set_page_config(page_title="Hospital Resource Analytics", page_icon="H", layout="wide")

st.markdown(
    """
    <style>
    .main {background-color: #f8fafc;}
    .kpi-card {background: white; border: 1px solid #d9e2ec; border-radius: 8px; padding: 16px; min-height: 112px;}
    .kpi-label {font-size: 0.82rem; color: #52616b; text-transform: uppercase; letter-spacing: .04em;}
    .kpi-value {font-size: 2rem; color: #102a43; font-weight: 700; margin-top: 8px;}
    .kpi-delta {font-size: .9rem; color: #2f855a; margin-top: 4px;}
    .block-container {padding-top: 1.4rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    patients = pd.read_csv(CLEAN_PATIENTS, parse_dates=["admission_date", "discharge_date"])
    daily = pd.read_csv(DAILY_DEPARTMENT, parse_dates=["date"])
    forecast = pd.read_csv(FORECAST_OUTPUT, parse_dates=["date"]) if FORECAST_OUTPUT.exists() else pd.DataFrame()
    recs = pd.read_csv(RECOMMENDATIONS_OUTPUT) if RECOMMENDATIONS_OUTPUT.exists() else pd.DataFrame()
    return patients, daily, forecast, recs


def filter_data(patients: pd.DataFrame, daily: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    st.sidebar.header("Filters")
    departments = sorted(patients["department"].unique())
    selected = st.sidebar.multiselect("Department", departments, default=departments)
    min_date, max_date = daily["date"].min().date(), daily["date"].max().date()
    date_range = st.sidebar.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if len(date_range) == 2:
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    else:
        start, end = pd.to_datetime(min_date), pd.to_datetime(max_date)
    p = patients[(patients["department"].isin(selected)) & (patients["admission_date"].between(start, end))]
    d = daily[(daily["department"].isin(selected)) & (daily["date"].between(start, end))]
    return p, d, selected


patients, daily, forecast, recs = load_data()
patients_f, daily_f, selected_departments = filter_data(patients, daily)

st.title("Hospital Resource Reallocation & Capacity Optimization")
st.caption("Consulting-style analytics system for capacity planning, wait-time reduction, and resource reallocation.")

uploaded = st.sidebar.file_uploader("Upload alternate patient CSV", type=["csv"])
if uploaded is not None:
    patients_f = pd.read_csv(uploaded)
    st.sidebar.success("Uploaded data loaded for exploratory views.")

cols = st.columns(5)
metrics = {
    "Patients": f"{len(patients_f):,}",
    "Avg Wait": f"{patients_f['wait_time_minutes'].mean():.1f} min",
    "Bed Occupancy": f"{daily_f['bed_occupancy_rate'].mean():.1%}",
    "ICU Utilization": f"{daily_f['icu_utilization_rate'].mean():.1%}",
    "Readmission": f"{patients_f['readmitted_30_days'].mean():.1%}",
}
for col, (label, value) in zip(cols, metrics.items()):
    col.markdown(kpi_card(label, value), unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Executive View", "Operations", "Forecasting", "Optimization", "Downloads"])

with tab1:
    c1, c2 = st.columns([1.15, 0.85])
    c1.plotly_chart(occupancy_trend(daily_f), use_container_width=True)
    c2.plotly_chart(department_comparison(daily_f), use_container_width=True)
    st.subheader("Management Findings")
    high_pressure = daily_f.groupby("department")["bed_occupancy_rate"].mean().sort_values(ascending=False).head(3)
    for dept, occ in high_pressure.items():
        st.write(f"- {dept}: average occupancy of {occ:.1%}, requiring active capacity monitoring.")

with tab2:
    c1, c2 = st.columns(2)
    c1.plotly_chart(wait_time_chart(patients_f), use_container_width=True)
    c2.plotly_chart(resource_heatmap(daily_f), use_container_width=True)
    st.dataframe(
        daily_f.groupby("department")
        .agg(
            occupancy=("bed_occupancy_rate", "mean"),
            icu=("icu_utilization_rate", "mean"),
            wait=("avg_wait_time", "mean"),
            equipment=("equipment_utilization_pct", "mean"),
            staff_ratio=("staff_to_patient_ratio", "mean"),
        )
        .sort_values("occupancy", ascending=False)
        .style.format({"occupancy": "{:.1%}", "icu": "{:.1%}", "wait": "{:.1f}", "equipment": "{:.1f}", "staff_ratio": "{:.2f}"}),
        use_container_width=True,
    )

with tab3:
    if forecast.empty:
        st.warning("Run `python main.py` to generate forecasting outputs.")
    else:
        dept = st.selectbox("Forecast department", sorted(forecast["department"].unique()))
        st.plotly_chart(forecast_chart(forecast, dept), use_container_width=True)
        st.dataframe(forecast[forecast["department"] == dept].tail(20), use_container_width=True)

with tab4:
    st.subheader("Resource Optimization Recommendations")
    if recs.empty:
        st.warning("Run `python main.py` to generate recommendations.")
    else:
        priority = st.multiselect("Priority", sorted(recs["priority"].unique()), default=sorted(recs["priority"].unique()))
        st.dataframe(recs[recs["priority"].isin(priority)], use_container_width=True)
    st.subheader("Scenario Simulator")
    increase = st.slider("What if ICU capacity increases by", 0, 30, 10, format="%d%%")
    scenario = simulate_icu_bed_increase(daily_f, increase / 100)
    icu_only = scenario[scenario["department"].eq("ICU")]
    st.metric("Average ICU utilization reduction", f"{icu_only['utilization_reduction_points'].mean():.1f} pts")

with tab5:
    st.download_button("Download filtered patient data", patients_f.to_csv(index=False), "filtered_patients.csv", "text/csv")
    st.download_button("Download filtered daily metrics", daily_f.to_csv(index=False), "filtered_daily_metrics.csv", "text/csv")
    if not recs.empty:
        st.download_button("Download recommendations", recs.to_csv(index=False), "optimization_recommendations.csv", "text/csv")
