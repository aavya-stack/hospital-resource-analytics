from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from src.config import SQLITE_DB


def build_sqlite_database(cleaned_paths: dict[str, Path]) -> Path:
    patients = pd.read_csv(cleaned_paths["patients"])
    resources = pd.read_csv(cleaned_paths["resources"])
    daily = pd.read_csv(cleaned_paths["daily"])
    with sqlite3.connect(SQLITE_DB) as conn:
        patients.to_sql("patients", conn, if_exists="replace", index=False)
        resources.to_sql("resources", conn, if_exists="replace", index=False)
        daily.to_sql("daily_department_metrics", conn, if_exists="replace", index=False)
        conn.executescript(
            """
            CREATE INDEX IF NOT EXISTS idx_patients_department ON patients(department);
            CREATE INDEX IF NOT EXISTS idx_patients_admission ON patients(admission_date);
            CREATE INDEX IF NOT EXISTS idx_resources_department_date ON resources(department, date);
            CREATE INDEX IF NOT EXISTS idx_daily_department_date ON daily_department_metrics(department, date);
            """
        )
    return SQLITE_DB
