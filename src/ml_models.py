from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import DATA_DIR, FORECAST_OUTPUT, REPORTS_DIR


def _metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 3),
        "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 3),
        "R2": round(float(r2_score(y_true, y_pred)), 3),
    }


def _calendar_features(df: pd.DataFrame, date_col: str) -> pd.DataFrame:
    out = df.copy()
    out["day_of_week"] = out[date_col].dt.dayofweek
    out["month"] = out[date_col].dt.month
    out["is_weekend"] = (out["day_of_week"] >= 5).astype(int)
    out["day_index"] = (out[date_col] - out[date_col].min()).dt.days
    return out


def train_wait_time_model(patients: pd.DataFrame) -> tuple[Pipeline, dict[str, float]]:
    features = ["age", "gender", "department", "severity", "emergency_case", "icu_requirement", "treatment_duration_days", "shift", "is_weekend"]
    target = "wait_time_minutes"
    X_train, X_test, y_train, y_test = train_test_split(patients[features], patients[target], test_size=0.2, random_state=42)
    categorical = ["gender", "department", "severity", "shift"]
    numeric = [c for c in features if c not in categorical]
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore"), categorical), ("num", StandardScaler(), numeric)])
    model = Pipeline([("preprocess", pre), ("model", RandomForestRegressor(n_estimators=120, min_samples_leaf=6, random_state=42, n_jobs=-1))])
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    return model, _metrics(y_test, preds)


def train_daily_forecast_model(daily: pd.DataFrame, target: str) -> tuple[Pipeline, dict[str, float], pd.DataFrame]:
    grouped = daily.groupby(["date", "department"], as_index=False).agg(
        target=(target, "mean"),
        admissions=("admissions", "sum"),
        emergency_cases=("emergency_cases", "sum"),
        staff_ratio=("staff_to_patient_ratio", "mean"),
        equipment_utilization=("equipment_utilization_pct", "mean"),
    )
    grouped = _calendar_features(grouped, "date").sort_values("date")
    grouped["target_lag_7"] = grouped.groupby("department")["target"].shift(7)
    grouped["target_roll_7"] = grouped.groupby("department")["target"].transform(lambda s: s.shift(1).rolling(7, min_periods=1).mean())
    grouped["target_lag_7"] = grouped["target_lag_7"].fillna(grouped.groupby("department")["target"].transform("mean"))
    grouped["target_roll_7"] = grouped["target_roll_7"].fillna(grouped.groupby("department")["target"].transform("mean"))
    features = ["department", "staff_ratio", "equipment_utilization", "day_of_week", "month", "is_weekend", "day_index", "target_lag_7", "target_roll_7"]
    if target != "admissions":
        features = ["department", "admissions", "emergency_cases", *features[1:]]
    split_date = grouped["date"].quantile(0.8)
    train = grouped[grouped["date"] <= split_date]
    test = grouped[grouped["date"] > split_date]
    pre = ColumnTransformer(
        [("dept", OneHotEncoder(handle_unknown="ignore"), ["department"]), ("num", StandardScaler(), [c for c in features if c != "department"])]
    )
    model = Pipeline([("preprocess", pre), ("model", Ridge(alpha=1.0))])
    model.fit(train[features], train["target"])
    preds = model.predict(test[features])
    forecast = test[["date", "department"]].copy()
    forecast[f"actual_{target}"] = test["target"].values
    forecast[f"predicted_{target}"] = preds
    return model, _metrics(test["target"], preds), forecast


def train_all_models(cleaned_paths: dict[str, Path]) -> dict[str, object]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    patients = pd.read_csv(cleaned_paths["patients"], parse_dates=["admission_date"])
    daily = pd.read_csv(cleaned_paths["daily"], parse_dates=["date"])
    wait_model, wait_metrics = train_wait_time_model(patients)
    bed_model, bed_metrics, bed_forecast = train_daily_forecast_model(daily, "bed_occupancy_rate")
    admission_model, admission_metrics, admission_forecast = train_daily_forecast_model(daily, "admissions")
    icu_model, icu_metrics, icu_forecast = train_daily_forecast_model(daily, "icu_utilization_rate")

    models_dir = DATA_DIR / "models"
    models_dir.mkdir(exist_ok=True)
    joblib.dump(wait_model, models_dir / "wait_time_model.joblib")
    joblib.dump(bed_model, models_dir / "bed_occupancy_model.joblib")
    joblib.dump(admission_model, models_dir / "admission_model.joblib")
    joblib.dump(icu_model, models_dir / "icu_demand_model.joblib")

    metrics = pd.DataFrame(
        [
            {"model": "Wait Time Prediction", **wait_metrics},
            {"model": "Bed Occupancy Forecasting", **bed_metrics},
            {"model": "Patient Admission Prediction", **admission_metrics},
            {"model": "ICU Demand Forecasting", **icu_metrics},
        ]
    )
    metrics_path = REPORTS_DIR / "model_evaluation_metrics.csv"
    metrics.to_csv(metrics_path, index=False)
    forecast = bed_forecast.merge(admission_forecast, on=["date", "department"]).merge(icu_forecast, on=["date", "department"])
    forecast.to_csv(FORECAST_OUTPUT, index=False)
    return {"metrics": metrics, "metrics_path": metrics_path, "forecast_path": FORECAST_OUTPUT}
