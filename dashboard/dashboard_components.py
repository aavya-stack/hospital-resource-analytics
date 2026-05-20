from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


CONSULTING_TEMPLATE = "plotly_white"


def kpi_card(label: str, value: str, delta: str | None = None) -> str:
    delta_html = f"<div class='kpi-delta'>{delta}</div>" if delta else ""
    return f"<div class='kpi-card'><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div>{delta_html}</div>"


def occupancy_trend(daily: pd.DataFrame) -> go.Figure:
    data = daily.groupby("date", as_index=False).agg(occupancy=("bed_occupancy_rate", "mean"))
    fig = px.line(data, x="date", y="occupancy", template=CONSULTING_TEMPLATE, title="Hospital Bed Occupancy Trend")
    fig.update_traces(line=dict(color="#1f4e79", width=3))
    fig.update_yaxes(tickformat=".0%")
    return fig


def department_comparison(daily: pd.DataFrame) -> go.Figure:
    data = daily.groupby("department", as_index=False).agg(occupancy=("bed_occupancy_rate", "mean"), wait=("avg_wait_time", "mean"))
    fig = px.scatter(
        data,
        x="occupancy",
        y="wait",
        size="wait",
        color="department",
        text="department",
        template=CONSULTING_TEMPLATE,
        title="Department Pressure Map: Occupancy vs Wait Time",
    )
    fig.update_xaxes(tickformat=".0%")
    fig.update_traces(textposition="top center")
    return fig


def wait_time_chart(patients: pd.DataFrame) -> go.Figure:
    fig = px.violin(
        patients,
        x="department",
        y="wait_time_minutes",
        color="department",
        box=True,
        template=CONSULTING_TEMPLATE,
        title="Wait-Time Distribution by Department",
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-35)
    return fig


def resource_heatmap(daily: pd.DataFrame) -> go.Figure:
    pivot = daily.pivot_table(index="department", columns=daily["date"].dt.day_name(), values="bed_occupancy_rate", aggfunc="mean")
    ordered = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot = pivot[[c for c in ordered if c in pivot.columns]]
    fig = px.imshow(pivot, aspect="auto", color_continuous_scale="RdYlGn_r", title="Average Occupancy Heatmap by Department and Day")
    return fig


def forecast_chart(forecast: pd.DataFrame, department: str) -> go.Figure:
    df = forecast[forecast["department"] == department].copy()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["date"], y=df["actual_bed_occupancy_rate"], mode="lines", name="Actual Occupancy"))
    fig.add_trace(go.Scatter(x=df["date"], y=df["predicted_bed_occupancy_rate"], mode="lines", name="Predicted Occupancy"))
    fig.update_layout(template=CONSULTING_TEMPLATE, title=f"Bed Occupancy Forecast: {department}", yaxis_tickformat=".0%")
    return fig
