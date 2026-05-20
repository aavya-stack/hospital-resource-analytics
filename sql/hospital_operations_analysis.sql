-- Hospital Resource Reallocation & Capacity Optimization Analytics System
-- SQLite-compatible consulting analysis pack.

-- 1. Department occupancy analysis
WITH department_occupancy AS (
    SELECT
        department,
        AVG(bed_occupancy_rate) AS avg_bed_occupancy,
        AVG(occupied_beds) AS avg_occupied_beds,
        AVG(available_beds) AS avg_available_beds
    FROM resources
    GROUP BY department
)
SELECT
    department,
    ROUND(avg_bed_occupancy * 100, 1) AS avg_bed_occupancy_pct,
    ROUND(avg_occupied_beds, 1) AS avg_occupied_beds,
    ROUND(avg_available_beds, 1) AS avg_available_beds,
    CASE
        WHEN avg_bed_occupancy >= 0.85 THEN 'Over-utilized'
        WHEN avg_bed_occupancy <= 0.65 THEN 'Under-utilized'
        ELSE 'Balanced'
    END AS utilization_status
FROM department_occupancy
ORDER BY avg_bed_occupancy DESC;

-- 2. Average patient wait time
SELECT
    department,
    severity,
    ROUND(AVG(wait_time_minutes), 1) AS avg_wait_time_minutes,
    COUNT(*) AS patients
FROM patients
GROUP BY department, severity
ORDER BY avg_wait_time_minutes DESC;

-- 3. ICU utilization rate
SELECT
    department,
    ROUND(AVG(icu_utilization_rate) * 100, 1) AS avg_icu_utilization_pct,
    ROUND(MAX(icu_utilization_rate) * 100, 1) AS peak_icu_utilization_pct
FROM resources
GROUP BY department
ORDER BY avg_icu_utilization_pct DESC;

-- 4. Peak admission periods
SELECT
    day_of_week,
    shift,
    COUNT(*) AS admissions,
    ROUND(AVG(wait_time_minutes), 1) AS avg_wait
FROM patients
GROUP BY day_of_week, shift
ORDER BY admissions DESC;

-- 5. Staff allocation efficiency
WITH staff_efficiency AS (
    SELECT
        r.department,
        r.date,
        r.occupied_beds,
        r.doctors_allocated,
        r.nurses_allocated,
        (r.doctors_allocated + r.nurses_allocated) * 1.0 / NULLIF(r.occupied_beds, 0) AS staff_to_patient_ratio,
        d.avg_wait_time
    FROM resources r
    JOIN daily_department_metrics d
        ON r.date = d.date AND r.department = d.department
)
SELECT
    department,
    ROUND(AVG(staff_to_patient_ratio), 2) AS avg_staff_to_patient_ratio,
    ROUND(AVG(avg_wait_time), 1) AS avg_wait_time,
    RANK() OVER (ORDER BY AVG(avg_wait_time) DESC) AS wait_pressure_rank
FROM staff_efficiency
GROUP BY department
ORDER BY wait_pressure_rank;

-- 6. Equipment utilization
SELECT
    department,
    ROUND(AVG(equipment_utilization_pct), 1) AS avg_equipment_utilization,
    ROUND(AVG(mri_usage), 1) AS avg_mri_usage,
    ROUND(AVG(ct_usage), 1) AS avg_ct_usage,
    SUM(CASE WHEN equipment_utilization_pct > 90 THEN 1 ELSE 0 END) AS high_utilization_days
FROM resources
GROUP BY department
ORDER BY high_utilization_days DESC;

-- 7. Monthly admission trends
SELECT
    admission_month,
    department,
    COUNT(*) AS admissions,
    ROUND(AVG(wait_time_minutes), 1) AS avg_wait_time,
    ROUND(AVG(cost_per_patient), 2) AS avg_cost
FROM patients
GROUP BY admission_month, department
ORDER BY admission_month, admissions DESC;

-- 8. Readmission analysis
SELECT
    department,
    disease_category,
    COUNT(*) AS cases,
    ROUND(AVG(readmitted_30_days) * 100, 1) AS readmission_rate_pct,
    ROUND(AVG(treatment_duration_days), 1) AS avg_treatment_days
FROM patients
GROUP BY department, disease_category
HAVING COUNT(*) >= 25
ORDER BY readmission_rate_pct DESC;

-- 9. Department-wise costs
SELECT
    department,
    COUNT(*) AS patients,
    ROUND(SUM(cost_per_patient), 2) AS total_cost,
    ROUND(AVG(cost_per_patient), 2) AS avg_cost_per_patient,
    ROUND(SUM(cost_per_patient) * 1.0 / SUM(treatment_duration_days), 2) AS cost_per_bed_day
FROM patients
GROUP BY department
ORDER BY total_cost DESC;

-- 10. Resource bottleneck detection
WITH bottlenecks AS (
    SELECT
        d.date,
        d.department,
        d.bed_occupancy_rate,
        d.icu_utilization_rate,
        d.avg_wait_time,
        d.equipment_utilization_pct,
        AVG(d.avg_wait_time) OVER (PARTITION BY d.department ORDER BY d.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7d_wait,
        AVG(d.bed_occupancy_rate) OVER (PARTITION BY d.department ORDER BY d.date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS rolling_7d_occupancy
    FROM daily_department_metrics d
)
SELECT
    date,
    department,
    ROUND(bed_occupancy_rate * 100, 1) AS occupancy_pct,
    ROUND(icu_utilization_rate * 100, 1) AS icu_utilization_pct,
    ROUND(avg_wait_time, 1) AS avg_wait_time,
    ROUND(equipment_utilization_pct, 1) AS equipment_utilization_pct,
    CASE
        WHEN rolling_7d_occupancy > 0.9 AND rolling_7d_wait > 90 THEN 'Critical capacity bottleneck'
        WHEN equipment_utilization_pct > 95 THEN 'Diagnostic equipment bottleneck'
        WHEN icu_utilization_rate > 0.9 THEN 'ICU bottleneck'
        ELSE 'Monitor'
    END AS bottleneck_type
FROM bottlenecks
WHERE rolling_7d_occupancy > 0.85
   OR rolling_7d_wait > 90
   OR equipment_utilization_pct > 95
   OR icu_utilization_rate > 0.9
ORDER BY date DESC, avg_wait_time DESC;
