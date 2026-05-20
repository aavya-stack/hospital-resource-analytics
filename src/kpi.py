from __future__ import annotations

from pathlib import Path

import pandas as pd


def calculate_kpis(cleaned_paths: dict[str, Path]) -> dict[str, object]:
    patients = pd.read_csv(cleaned_paths["patients"], parse_dates=["admission_date"])
    daily = pd.read_csv(cleaned_paths["daily"], parse_dates=["date"])
    dept = (
        daily.groupby("department")
        .agg(
            avg_bed_occupancy=("bed_occupancy_rate", "mean"),
            avg_icu_utilization=("icu_utilization_rate", "mean"),
            avg_wait_time=("avg_wait_time", "mean"),
            admissions=("admissions", "sum"),
            avg_equipment_utilization=("equipment_utilization_pct", "mean"),
            avg_staff_ratio=("staff_to_patient_ratio", "mean"),
            avg_cost=("avg_cost", "mean"),
            readmission_rate=("readmission_rate", "mean"),
        )
        .reset_index()
    )
    over = dept[dept["avg_bed_occupancy"] > 0.85]["department"].tolist()
    under = dept[dept["avg_bed_occupancy"] < 0.65]["department"].tolist()
    kpis = {
        "total_patients": int(len(patients)),
        "avg_wait_time": round(float(patients["wait_time_minutes"].mean()), 1),
        "avg_bed_occupancy": round(float(daily["bed_occupancy_rate"].mean() * 100), 1),
        "avg_icu_utilization": round(float(daily["icu_utilization_rate"].mean() * 100), 1),
        "readmission_rate": round(float(patients["readmitted_30_days"].mean() * 100), 1),
        "emergency_share": round(float(patients["emergency_case"].mean() * 100), 1),
        "avg_cost_per_patient": round(float(patients["cost_per_patient"].mean()), 2),
        "over_utilized_departments": over,
        "under_utilized_departments": under,
        "department_table": dept.sort_values("avg_bed_occupancy", ascending=False),
    }
    return kpis
