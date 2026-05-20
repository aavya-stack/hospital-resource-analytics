from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import CLEAN_PATIENTS, CLEAN_RESOURCES, DAILY_DEPARTMENT


def clean_patients(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["admission_date", "discharge_date"])
    df = df.drop_duplicates(subset=["patient_id"]).copy()
    df["department"] = df["department"].str.strip()
    df["gender"] = df["gender"].fillna("Unknown")
    df["disease_category"] = df["disease_category"].fillna("Unclassified")
    df["age"] = df.groupby("department")["age"].transform(lambda s: s.fillna(s.median())).clip(0, 100)
    df["wait_time_minutes"] = df.groupby("department")["wait_time_minutes"].transform(lambda s: s.fillna(s.median())).clip(0)
    df["cost_per_patient"] = df.groupby("department")["cost_per_patient"].transform(lambda s: s.fillna(s.median())).clip(lower=0)
    df["length_of_stay_days"] = (df["discharge_date"] - df["admission_date"]).dt.days.clip(lower=1)
    df["admission_month"] = df["admission_date"].dt.to_period("M").astype(str)
    df["day_of_week"] = df["admission_date"].dt.day_name()
    df["is_weekend"] = df["admission_date"].dt.weekday >= 5
    df["wait_time_flag"] = pd.cut(
        df["wait_time_minutes"],
        bins=[-1, 30, 60, 120, 10000],
        labels=["Fast", "Moderate", "Delayed", "Critical Delay"],
    )
    return df


def clean_resources(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    numeric_cols = df.select_dtypes(include=["number"]).columns
    for col in numeric_cols:
        df[col] = df.groupby("department")[col].transform(lambda s: s.fillna(s.median()))
    df["bed_occupancy_rate"] = (df["occupied_beds"] / df["bed_capacity"]).clip(0, 1.4)
    df["icu_utilization_rate"] = (df["icu_occupancy"] / df["icu_capacity"]).replace([float("inf")], 0).clip(0, 1.4)
    df["staff_to_patient_ratio"] = ((df["doctors_allocated"] + df["nurses_allocated"]) / df["occupied_beds"].replace(0, 1)).round(2)
    df["nurse_to_patient_ratio"] = (df["nurses_allocated"] / df["occupied_beds"].replace(0, 1)).round(2)
    df["resource_status"] = pd.cut(
        df["bed_occupancy_rate"],
        bins=[-0.1, 0.65, 0.85, 1.5],
        labels=["Under-utilized", "Balanced", "Over-utilized"],
    )
    return df


def build_daily_department_metrics(patients: pd.DataFrame, resources: pd.DataFrame) -> pd.DataFrame:
    patient_daily = (
        patients.groupby([patients["admission_date"].dt.date, "department"])
        .agg(
            admissions=("patient_id", "count"),
            avg_wait_time=("wait_time_minutes", "mean"),
            emergency_cases=("emergency_case", "sum"),
            avg_treatment_duration=("treatment_duration_days", "mean"),
            readmission_rate=("readmitted_30_days", "mean"),
            avg_cost=("cost_per_patient", "mean"),
            icu_required=("icu_requirement", "sum"),
        )
        .reset_index()
        .rename(columns={"admission_date": "date"})
    )
    patient_daily["date"] = pd.to_datetime(patient_daily["date"])
    merged = resources.merge(patient_daily, on=["date", "department"], how="left")
    fill_cols = ["admissions", "avg_wait_time", "emergency_cases", "avg_treatment_duration", "readmission_rate", "avg_cost", "icu_required"]
    merged[fill_cols] = merged[fill_cols].fillna(0)
    return merged


def clean_and_save_data(raw_paths: dict[str, Path]) -> dict[str, Path]:
    patients = clean_patients(raw_paths["patients"])
    resources = clean_resources(raw_paths["resources"])
    daily = build_daily_department_metrics(patients, resources)
    patients.to_csv(CLEAN_PATIENTS, index=False)
    resources.to_csv(CLEAN_RESOURCES, index=False)
    daily.to_csv(DAILY_DEPARTMENT, index=False)
    return {"patients": CLEAN_PATIENTS, "resources": CLEAN_RESOURCES, "daily": DAILY_DEPARTMENT}
