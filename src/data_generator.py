from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DATA_DIR, DEPARTMENT_CAPACITY, DEPARTMENTS, N_PATIENTS, RANDOM_SEED, RAW_PATIENTS, RAW_RESOURCES


def _date_range() -> pd.DatetimeIndex:
    return pd.date_range("2024-01-01", "2025-12-31", freq="D")


def generate_patient_data(n_patients: int = N_PATIENTS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = _date_range()
    dept_probs = np.array([0.18, 0.08, 0.10, 0.09, 0.18, 0.07, 0.08, 0.06, 0.10, 0.06])
    disease_map = {
        "Emergency": ["Trauma", "Chest Pain", "Stroke Alert", "Respiratory Distress", "Sepsis"],
        "ICU": ["Sepsis", "Respiratory Failure", "Post-operative Critical", "Cardiac Arrest"],
        "Cardiology": ["Heart Failure", "Arrhythmia", "Acute Coronary Syndrome", "Hypertension"],
        "Orthopedics": ["Fracture", "Joint Replacement", "Spine Injury", "Sports Injury"],
        "General Medicine": ["Diabetes", "Pneumonia", "Infection", "Kidney Disease", "Gastroenteritis"],
        "Neurology": ["Stroke", "Epilepsy", "Migraine", "Neuropathy"],
        "Pediatrics": ["Fever", "Asthma", "Dehydration", "Infection"],
        "Oncology": ["Chemotherapy", "Tumor Evaluation", "Radiation Support", "Neutropenia"],
        "Surgery": ["Appendicitis", "Gallbladder", "Hernia", "Post-op Care"],
        "Maternity": ["Labor", "Antenatal Care", "C-section", "Postnatal Care"],
    }
    severity_multiplier = {"Low": 0.75, "Medium": 1.0, "High": 1.45, "Critical": 2.15}
    departments = rng.choice(DEPARTMENTS, size=n_patients, p=dept_probs)
    admission_dates = rng.choice(dates, size=n_patients)
    admission_dates = pd.to_datetime(admission_dates)
    weekday = admission_dates.weekday
    month = admission_dates.month
    is_weekend = weekday >= 5
    season_pressure = np.where(np.isin(month, [1, 2, 7, 8, 12]), 1.18, 1.0)
    emergency = rng.binomial(1, np.where(departments == "Emergency", 0.72, 0.14))
    severity = rng.choice(["Low", "Medium", "High", "Critical"], n_patients, p=[0.34, 0.42, 0.18, 0.06])
    ages = np.clip(rng.normal(49, 22, n_patients), 0, 96).round().astype(int)
    gender = rng.choice(["Female", "Male", "Other"], n_patients, p=[0.51, 0.48, 0.01])
    base_wait = {
        "Emergency": 95,
        "ICU": 40,
        "Cardiology": 58,
        "Orthopedics": 72,
        "General Medicine": 66,
        "Neurology": 70,
        "Pediatrics": 45,
        "Oncology": 38,
        "Surgery": 63,
        "Maternity": 34,
    }
    wait_times = []
    treatment_days = []
    icu_requirement = []
    readmitted = []
    costs = []
    diseases = []
    for dept, sev, age, weekend, pressure, emerg in zip(departments, severity, ages, is_weekend, season_pressure, emergency):
        inefficiency = 1.24 if dept in ["Emergency", "ICU", "Neurology"] and weekend else 1.0
        queue_noise = rng.gamma(shape=2.0, scale=14.0)
        wait = (base_wait[dept] * severity_multiplier[sev] * pressure * inefficiency) + queue_noise - (emerg * 18)
        wait_times.append(max(5, round(wait, 1)))
        los_base = {"ICU": 8, "Oncology": 6, "Surgery": 5, "Cardiology": 4, "Neurology": 4, "General Medicine": 4}.get(dept, 3)
        los = max(1, int(rng.gamma(los_base / 1.7, 1.7) * severity_multiplier[sev]))
        treatment_days.append(min(los, 35))
        icu_prob = 0.75 if dept == "ICU" else 0.06 + 0.12 * (sev == "High") + 0.3 * (sev == "Critical") + 0.06 * (age > 70)
        icu_requirement.append(int(rng.random() < min(0.9, icu_prob)))
        readmitted.append(int(rng.random() < (0.06 + 0.05 * (sev in ["High", "Critical"]) + 0.03 * (age > 65))))
        costs.append(round(rng.normal(2400, 420) + los * rng.normal(970, 120) + wait * 4 + (dept == "ICU") * 5200, 2))
        diseases.append(rng.choice(disease_map[dept]))
    discharge_dates = admission_dates + pd.to_timedelta(treatment_days, unit="D")
    df = pd.DataFrame(
        {
            "patient_id": [f"P{100000 + i}" for i in range(n_patients)],
            "age": ages,
            "gender": gender,
            "disease_category": diseases,
            "severity": severity,
            "admission_date": admission_dates,
            "discharge_date": discharge_dates,
            "wait_time_minutes": wait_times,
            "department": departments,
            "icu_requirement": icu_requirement,
            "emergency_case": emergency,
            "treatment_duration_days": treatment_days,
            "readmitted_30_days": readmitted,
            "cost_per_patient": np.maximum(costs, 700).round(2),
            "shift": rng.choice(["Morning", "Afternoon", "Evening", "Night"], n_patients, p=[0.29, 0.26, 0.27, 0.18]),
        }
    )
    for col, frac in [("age", 0.012), ("wait_time_minutes", 0.018), ("disease_category", 0.009), ("cost_per_patient", 0.01)]:
        idx = rng.choice(df.index, size=int(len(df) * frac), replace=False)
        df.loc[idx, col] = np.nan
    return df


def generate_resource_data(patient_df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 7)
    records = []
    daily_load = patient_df.groupby([pd.to_datetime(patient_df["admission_date"]).dt.date, "department"]).size().reset_index(name="admissions")
    daily_load["date"] = pd.to_datetime(daily_load["admission_date"])
    target_occupancy = {
        "Emergency": 0.88,
        "ICU": 0.91,
        "Cardiology": 0.76,
        "Orthopedics": 0.68,
        "General Medicine": 0.81,
        "Neurology": 0.79,
        "Pediatrics": 0.66,
        "Oncology": 0.72,
        "Surgery": 0.77,
        "Maternity": 0.62,
    }
    for date in _date_range():
        for dept in DEPARTMENTS:
            cap = DEPARTMENT_CAPACITY[dept]
            load_row = daily_load[(daily_load["date"] == date) & (daily_load["department"] == dept)]
            admissions = int(load_row["admissions"].iloc[0]) if len(load_row) else 0
            weekend_lift = 0.07 if date.weekday() >= 5 and dept in ["Emergency", "ICU", "General Medicine"] else 0.0
            winter_lift = 0.05 if date.month in [1, 2, 7, 8, 12] and dept in ["Emergency", "ICU", "Pediatrics"] else 0.0
            admission_lift = min(0.10, admissions / max(cap["beds"], 1) * 0.9)
            occ_rate = np.clip(target_occupancy[dept] + weekend_lift + winter_lift + admission_lift + rng.normal(0, 0.055), 0.38, 1.08)
            occupancy = min(cap["beds"], max(0, int(round(cap["beds"] * occ_rate))))
            icu_rate = 0.9 if dept == "ICU" else 0.08 + 0.18 * (dept in ["Emergency", "Cardiology", "Surgery"])
            icu_occupancy = min(cap["ventilators"] + 4, max(0, int(round((cap["ventilators"] + (3 if dept == "ICU" else 0)) * icu_rate + rng.normal(0, 1.3)))))
            equipment_pressure = min(1.25, occ_rate + admissions / max(cap["ct_slots"], 1) * 0.20 + rng.normal(0.03, 0.06))
            records.append(
                {
                    "date": date,
                    "department": dept,
                    "bed_capacity": cap["beds"],
                    "occupied_beds": occupancy,
                    "available_beds": max(0, cap["beds"] - occupancy),
                    "icu_capacity": cap["ventilators"] + (3 if dept == "ICU" else 0),
                    "icu_occupancy": icu_occupancy,
                    "doctors_allocated": max(1, int(rng.normal(cap["doctors"], 2))),
                    "nurses_allocated": max(2, int(rng.normal(cap["nurses"], 4))),
                    "equipment_utilization_pct": round(float(np.clip(58 + equipment_pressure * 32 + rng.normal(0, 8), 15, 118)), 1),
                    "mri_usage": max(0, int(rng.normal(cap["mri_slots"] * min(1.15, equipment_pressure), 2))),
                    "ct_usage": max(0, int(rng.normal(cap["ct_slots"] * min(1.20, equipment_pressure), 4))),
                    "ventilator_available": max(0, cap["ventilators"] - icu_occupancy),
                    "daily_admissions": admissions,
                }
            )
    df = pd.DataFrame(records)
    miss_idx = rng.choice(df.index, size=int(len(df) * 0.008), replace=False)
    df.loc[miss_idx, "equipment_utilization_pct"] = np.nan
    return df


def generate_all_data() -> dict[str, Path]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    patients = generate_patient_data()
    resources = generate_resource_data(patients)
    patients.to_csv(RAW_PATIENTS, index=False)
    resources.to_csv(RAW_RESOURCES, index=False)
    return {"patients": RAW_PATIENTS, "resources": RAW_RESOURCES}
