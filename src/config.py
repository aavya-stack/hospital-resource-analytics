from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"
SQL_DIR = PROJECT_ROOT / "sql"
APP_DIR = PROJECT_ROOT / "app"
SCREENSHOTS_DIR = PROJECT_ROOT / "screenshots"

RAW_PATIENTS = DATA_DIR / "raw_patients.csv"
RAW_RESOURCES = DATA_DIR / "raw_resources.csv"
CLEAN_PATIENTS = DATA_DIR / "clean_patients.csv"
CLEAN_RESOURCES = DATA_DIR / "clean_resources.csv"
DAILY_DEPARTMENT = DATA_DIR / "daily_department_metrics.csv"
FORECAST_OUTPUT = DATA_DIR / "forecast_outputs.csv"
RECOMMENDATIONS_OUTPUT = DATA_DIR / "optimization_recommendations.csv"
SQLITE_DB = DATA_DIR / "hospital_operations.db"

RANDOM_SEED = 42
N_PATIENTS = 12000

DEPARTMENTS = [
    "Emergency",
    "ICU",
    "Cardiology",
    "Orthopedics",
    "General Medicine",
    "Neurology",
    "Pediatrics",
    "Oncology",
    "Surgery",
    "Maternity",
]

DEPARTMENT_CAPACITY = {
    "Emergency": {"beds": 58, "doctors": 22, "nurses": 54, "mri_slots": 10, "ct_slots": 30, "ventilators": 8},
    "ICU": {"beds": 34, "doctors": 18, "nurses": 64, "mri_slots": 4, "ct_slots": 12, "ventilators": 31},
    "Cardiology": {"beds": 48, "doctors": 15, "nurses": 38, "mri_slots": 6, "ct_slots": 14, "ventilators": 10},
    "Orthopedics": {"beds": 44, "doctors": 12, "nurses": 30, "mri_slots": 9, "ct_slots": 10, "ventilators": 2},
    "General Medicine": {"beds": 76, "doctors": 20, "nurses": 52, "mri_slots": 5, "ct_slots": 16, "ventilators": 5},
    "Neurology": {"beds": 36, "doctors": 12, "nurses": 28, "mri_slots": 12, "ct_slots": 12, "ventilators": 5},
    "Pediatrics": {"beds": 42, "doctors": 13, "nurses": 34, "mri_slots": 4, "ct_slots": 9, "ventilators": 6},
    "Oncology": {"beds": 40, "doctors": 11, "nurses": 30, "mri_slots": 5, "ct_slots": 8, "ventilators": 3},
    "Surgery": {"beds": 52, "doctors": 18, "nurses": 42, "mri_slots": 5, "ct_slots": 15, "ventilators": 8},
    "Maternity": {"beds": 46, "doctors": 14, "nurses": 36, "mri_slots": 2, "ct_slots": 5, "ventilators": 4},
}
