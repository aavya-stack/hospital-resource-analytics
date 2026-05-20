from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.config import RECOMMENDATIONS_OUTPUT


def build_recommendations(cleaned_paths: dict[str, Path], kpis: dict[str, object], model_outputs: dict[str, object]) -> pd.DataFrame:
    daily = pd.read_csv(cleaned_paths["daily"], parse_dates=["date"])
    dept = (
        daily.groupby("department")
        .agg(
            occupancy=("bed_occupancy_rate", "mean"),
            wait=("avg_wait_time", "mean"),
            icu=("icu_utilization_rate", "mean"),
            staff_ratio=("staff_to_patient_ratio", "mean"),
            nurses=("nurses_allocated", "mean"),
            doctors=("doctors_allocated", "mean"),
            equipment=("equipment_utilization_pct", "mean"),
            weekend_admissions=("admissions", lambda s: s[daily.loc[s.index, "date"].dt.weekday >= 5].sum()),
        )
        .reset_index()
    )
    over = dept[dept["occupancy"] > 0.85].sort_values("occupancy", ascending=False)
    under = dept[dept["occupancy"] < 0.65].sort_values("occupancy")
    recommendations = []
    for _, row in over.iterrows():
        donor = under.iloc[0] if len(under) else dept.sort_values("staff_ratio", ascending=False).iloc[0]
        nurse_move = max(2, int(round(row["nurses"] * 0.08)))
        bed_increase = max(3, int(round(row["occupancy"] * 8)))
        recommendations.append(
            {
                "priority": "High",
                "area": row["department"],
                "recommendation": f"Move {nurse_move} nurses from {donor['department']} to {row['department']} during evening and weekend peaks.",
                "rationale": f"{row['department']} average occupancy is {row['occupancy']:.0%} with {row['wait']:.1f} minute average waits.",
                "estimated_impact": "Expected 10-18% wait-time reduction and improved throughput during surge windows.",
            }
        )
        recommendations.append(
            {
                "priority": "High",
                "area": row["department"],
                "recommendation": f"Create a flexible surge pool of {bed_increase} beds for {row['department']} and adjacent high-acuity pathways.",
                "rationale": "Sustained occupancy above 85% increases boarding risk and delays discharges.",
                "estimated_impact": "Expected 6-12% improvement in bed availability and lower left-without-being-seen risk.",
            }
        )
    for _, row in dept[dept["equipment"] > 88].iterrows():
        recommendations.append(
            {
                "priority": "Medium",
                "area": row["department"],
                "recommendation": f"Add protected diagnostic blocks for {row['department']} and shift non-urgent MRI/CT to low-demand mornings.",
                "rationale": f"Equipment utilization averages {row['equipment']:.1f}%, indicating scheduling bottlenecks.",
                "estimated_impact": "Expected 8-15% reduction in diagnostic turnaround time.",
            }
        )
    if not recommendations:
        recommendations.append(
            {
                "priority": "Medium",
                "area": "Hospital-wide",
                "recommendation": "Maintain flexible cross-trained nursing pool and weekly capacity huddles.",
                "rationale": "Overall utilization is balanced, but demand volatility remains material.",
                "estimated_impact": "Preserves service resilience and reduces surge overtime.",
            }
        )
    rec_df = pd.DataFrame(recommendations).drop_duplicates()
    rec_df.to_csv(RECOMMENDATIONS_OUTPUT, index=False)
    return rec_df


def simulate_icu_bed_increase(daily: pd.DataFrame, increase_pct: float = 0.10) -> pd.DataFrame:
    scenario = daily.copy()
    icu_mask = scenario["department"].eq("ICU")
    scenario.loc[icu_mask, "scenario_icu_capacity"] = scenario.loc[icu_mask, "icu_capacity"] * (1 + increase_pct)
    scenario.loc[~icu_mask, "scenario_icu_capacity"] = scenario.loc[~icu_mask, "icu_capacity"]
    scenario["scenario_icu_utilization"] = scenario["icu_occupancy"] / scenario["scenario_icu_capacity"].replace(0, 1)
    scenario["utilization_reduction_points"] = (scenario["icu_utilization_rate"] - scenario["scenario_icu_utilization"]) * 100
    return scenario
