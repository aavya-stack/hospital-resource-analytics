from pathlib import Path

from src.config import PROJECT_ROOT
from src.data_generator import generate_all_data
from src.data_cleaning import clean_and_save_data
from src.database import build_sqlite_database
from src.eda import run_eda
from src.kpi import calculate_kpis
from src.ml_models import train_all_models
from src.optimization import build_recommendations
from src.report_generator import generate_executive_report


def main() -> None:
    print("Hospital Resource Reallocation & Capacity Optimization Analytics System")
    print(f"Project root: {PROJECT_ROOT}")

    raw_paths = generate_all_data()
    cleaned_paths = clean_and_save_data(raw_paths)
    db_path = build_sqlite_database(cleaned_paths)
    kpis = calculate_kpis(cleaned_paths)
    eda_outputs = run_eda(cleaned_paths)
    model_outputs = train_all_models(cleaned_paths)
    recommendations = build_recommendations(cleaned_paths, kpis, model_outputs)
    report_path = generate_executive_report(kpis, recommendations, model_outputs)

    print("\nPipeline complete.")
    print(f"SQLite database: {db_path}")
    print(f"Executive report: {report_path}")
    print("Dashboard: streamlit run app/streamlit_app.py")
    print("Key output folders: data/, reports/, dashboard/, sql/")


if __name__ == "__main__":
    main()
