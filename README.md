# Hospital Resource Reallocation & Capacity Optimization Analytics System

An end-to-end healthcare consulting analytics project that simulates a hospital operations engagement. The system analyzes patient flow, department utilization, bed and ICU pressure, staff allocation, equipment bottlenecks, wait-time drivers, and future demand to recommend practical resource reallocation actions.

## Business Objective

Hospital leadership needs to answer six operational questions:

1. Which departments are over-utilized or under-utilized?
2. How should beds, nurses, doctors, and diagnostic equipment be reallocated?
3. What factors contribute to long patient waiting times?
4. How can operational efficiency and patient throughput improve?
5. Can future admissions, occupancy, and ICU demand be predicted?
6. What strategic actions should executives prioritize?

## Portfolio Highlights

- Synthetic but realistic healthcare operations dataset with 12,000+ patient records and two years of daily resource metrics
- Data cleaning pipeline with missing value treatment, derived features, and quality checks
- SQLite database with indexed analytical tables
- SQL analysis pack using CTEs, joins, aggregations, and window functions
- EDA outputs covering occupancy, patient flow, wait-time distribution, peak load, and correlations
- Machine learning models for wait-time prediction, admissions, bed occupancy, and ICU demand forecasting
- Optimization recommendation engine for staff, bed, and diagnostic capacity reallocation
- Streamlit consulting dashboard with filters, forecasting, scenario simulation, and downloads
- Executive summary in Markdown and PDF formats
- Power BI-compatible CSV outputs

## Tech Stack

Python, Pandas, NumPy, SQLite, SQL, Scikit-learn, Plotly, Seaborn, Matplotlib, Streamlit, ReportLab, Joblib

## Project Architecture

```text
hospital-resource-analytics/
|-- data/
|-- notebooks/
|-- sql/
|-- src/
|-- dashboard/
|-- reports/
|-- screenshots/
|-- app/
|-- requirements.txt
|-- README.md
`-- main.py
```

## Dataset

The project generates synthetic data when no real hospital dataset is available.

Patient data includes patient ID, age, gender, disease category, severity, admission/discharge dates, wait time, department, ICU requirement, emergency flag, treatment duration, readmission, cost, and shift.

Resource data includes bed capacity, occupied and available beds, ICU occupancy, doctors, nurses, equipment utilization, MRI/CT usage, ventilator availability, and daily admissions.

Operational inefficiencies are intentionally simulated, including weekend emergency surges, high ICU pressure, equipment bottlenecks, missing values, seasonal demand, and department-level imbalance.

## Installation

```bash
cd hospital-resource-analytics
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Run the full analytics pipeline:

```bash
python main.py
```

Launch the Streamlit dashboard:

```bash
streamlit run app/streamlit_app.py
```

## Workflow

1. `src/data_generator.py` creates realistic patient and resource datasets.
2. `src/data_cleaning.py` cleans missing values and builds daily department metrics.
3. `src/database.py` loads cleaned tables into SQLite.
4. `src/eda.py` creates professional exploratory charts and quality outputs.
5. `src/kpi.py` calculates executive KPIs and department utilization status.
6. `src/ml_models.py` trains regression and time-series style forecasting models.
7. `src/optimization.py` generates operational recommendations and scenario simulation.
8. `src/report_generator.py` creates an executive summary report.
9. `app/streamlit_app.py` serves an interactive consulting dashboard.

## SQL Analysis

The file `sql/hospital_operations_analysis.sql` includes:

- Department occupancy analysis
- Average patient wait time
- ICU utilization rate
- Peak admission periods
- Staff allocation efficiency
- Equipment utilization
- Monthly admission trends
- Readmission analysis
- Department-wise costs
- Resource bottleneck detection

## Machine Learning

Models included:

- Wait time prediction using Random Forest regression
- Bed occupancy forecasting using time-aware features and Ridge regression
- Patient admission prediction
- ICU demand forecasting

Evaluation metrics are saved to `reports/model_evaluation_metrics.csv` and include MAE, RMSE, and R2.

## Dashboard Features

- Executive KPI cards
- Department pressure map
- Occupancy trend analysis
- Wait-time distribution
- Resource utilization heatmap
- Forecasting charts
- ICU capacity scenario simulator
- Optimization recommendations
- CSV upload and downloadable outputs

## Consulting Insights Generated

Example recommendation themes:

- Move nurses from under-utilized departments to peak-pressure departments during evening and weekend surges.
- Create flexible surge beds for departments with sustained occupancy above 85%.
- Shift non-urgent MRI/CT appointments to low-demand windows when equipment utilization exceeds 90%.
- Use a weekly capacity control tower to coordinate staffing, discharge planning, and diagnostic scheduling.

## Screenshot Placeholders

Add screenshots after running the app:

- `screenshots/executive_dashboard.png`
- `screenshots/operations_tab.png`
- `screenshots/forecasting_tab.png`
- `screenshots/optimization_tab.png`

## Key Outputs

- `data/raw_patients.csv`
- `data/raw_resources.csv`
- `data/clean_patients.csv`
- `data/clean_resources.csv`
- `data/daily_department_metrics.csv`
- `data/hospital_operations.db`
- `data/forecast_outputs.csv`
- `data/optimization_recommendations.csv`
- `reports/executive_summary.md`
- `reports/executive_summary.pdf`
- `reports/model_evaluation_metrics.csv`
- `dashboard/*.html`

## Resume-Worthy Description

Built a production-style healthcare analytics system to optimize hospital capacity, reduce patient wait times, forecast demand, and recommend resource reallocation using Python, SQL, machine learning, Streamlit, and consulting-grade executive reporting.

## Future Improvements

- Add live EHR and bed-management system integration
- Deploy dashboard on Streamlit Community Cloud
- Add hospital-level financial simulation with payer mix and margin assumptions
- Extend optimization with linear programming for staffing constraints
- Add anomaly alerts for surges, bed shortages, and diagnostic equipment backlogs
