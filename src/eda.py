from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns

from src.config import DASHBOARD_DIR, REPORTS_DIR


def _save_plotly(fig, name: str) -> Path:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    path = DASHBOARD_DIR / name
    fig.write_html(path, include_plotlyjs="cdn")
    return path


def run_eda(cleaned_paths: dict[str, Path]) -> dict[str, Path]:
    patients = pd.read_csv(cleaned_paths["patients"], parse_dates=["admission_date"])
    daily = pd.read_csv(cleaned_paths["daily"], parse_dates=["date"])
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}

    missing = patients.isna().mean().sort_values(ascending=False).reset_index()
    missing.columns = ["column", "missing_rate"]
    missing_path = REPORTS_DIR / "missing_value_analysis.csv"
    missing.to_csv(missing_path, index=False)
    outputs["missing_values"] = missing_path

    fig = px.line(
        daily.groupby("date", as_index=False).agg(avg_occupancy=("bed_occupancy_rate", "mean"), admissions=("admissions", "sum")),
        x="date",
        y=["avg_occupancy", "admissions"],
        title="Hospital Occupancy and Admission Trend",
        template="plotly_white",
    )
    outputs["occupancy_trend"] = _save_plotly(fig, "occupancy_trend.html")

    fig = px.box(patients, x="department", y="wait_time_minutes", color="department", title="Wait Time Distribution by Department", template="plotly_white")
    fig.update_layout(showlegend=False, xaxis_tickangle=-35)
    outputs["wait_distribution"] = _save_plotly(fig, "wait_time_distribution.html")

    fig = px.bar(
        daily.groupby("department", as_index=False).agg(avg_occupancy=("bed_occupancy_rate", "mean"), avg_wait=("avg_wait_time", "mean")),
        x="department",
        y="avg_occupancy",
        color="avg_wait",
        title="Department Occupancy vs Wait-Time Pressure",
        template="plotly_white",
        color_continuous_scale="RdYlGn_r",
    )
    fig.update_layout(xaxis_tickangle=-35)
    outputs["department_pressure"] = _save_plotly(fig, "department_pressure.html")

    corr_cols = ["age", "wait_time_minutes", "icu_requirement", "emergency_case", "treatment_duration_days", "readmitted_30_days", "cost_per_patient"]
    plt.figure(figsize=(10, 7))
    sns.heatmap(patients[corr_cols].corr(numeric_only=True), annot=True, fmt=".2f", cmap="vlag", center=0)
    plt.title("Patient and Operational Correlation Heatmap")
    plt.tight_layout()
    corr_path = REPORTS_DIR / "correlation_heatmap.png"
    plt.savefig(corr_path, dpi=180)
    plt.close()
    outputs["correlation_heatmap"] = corr_path

    peak = patients.groupby(["day_of_week", "shift"]).size().reset_index(name="admissions")
    fig = px.density_heatmap(peak, x="shift", y="day_of_week", z="admissions", title="Peak Admission Heatmap", template="plotly_white")
    outputs["peak_heatmap"] = _save_plotly(fig, "peak_admission_heatmap.html")
    return outputs
