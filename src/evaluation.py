import pandas as pd


def compare_rule_alerts_with_insiders_top_k(
    alerts_csv,
    insiders_csv,
    output_csv="evaluate_alerts_top_k.csv",
    k=100
):
    alerts = pd.read_csv(alerts_csv)
    insiders = pd.read_csv(insiders_csv)

    # Column names
    alert_user_col = "user"
    alert_date_col = "day"
    alert_risk_col = "risk_level"

    insider_user_col = "user"
    insider_start_col = "start"
    insider_end_col = "end"

    # Clean user columns
    alerts[alert_user_col] = alerts[alert_user_col].astype(str).str.strip()
    insiders[insider_user_col] = insiders[insider_user_col].astype(str).str.strip()

    # Convert dates safely
    alerts[alert_date_col] = pd.to_datetime(
        alerts[alert_date_col],
        errors="coerce",
        format="mixed"
    )

    insiders[insider_start_col] = pd.to_datetime(
        insiders[insider_start_col],
        errors="coerce",
        format="mixed"
    )

    insiders[insider_end_col] = pd.to_datetime(
        insiders[insider_end_col],
        errors="coerce",
        format="mixed"
    )

    # Remove invalid dates
    alerts = alerts.dropna(subset=[alert_date_col]).copy()
    insiders = insiders.dropna(
        subset=[insider_start_col, insider_end_col]
    ).copy()

    # Rank risk levels for Top K selection
    risk_order = {
        "Critical": 4,
        "High": 3,
        "Medium": 2,
        "Low": 1
    }

    alerts["risk_rank"] = (
        alerts[alert_risk_col]
        .astype(str)
        .str.strip()
        .map(risk_order)
        .fillna(0)
    )

    # Select Top K alerts
    alerts = alerts.sort_values(
        by=["risk_rank", alert_date_col],
        ascending=[False, True]
    ).head(k).copy()

    alerts["rank"] = range(1, len(alerts) + 1)

    # Default labels
    alerts["is_known_insider"] = False
    alerts["matched_insider_window"] = ""

    # Match alert user/date with insider user/date window
    for i, alert in alerts.iterrows():
        user = alert[alert_user_col]
        alert_day = alert[alert_date_col]

        match = insiders[
            (insiders[insider_user_col] == user) &
            (insiders[insider_start_col] <= alert_day) &
            (insiders[insider_end_col] >= alert_day)
        ]

        if not match.empty:
            alerts.at[i, "is_known_insider"] = True

            first_match = match.iloc[0]
            alerts.at[i, "matched_insider_window"] = (
                f"{first_match[insider_start_col].date()} to "
                f"{first_match[insider_end_col].date()}"
            )

    # Metrics
    total_top_k = len(alerts)
    true_positives = alerts["is_known_insider"].sum()
    false_positives = total_top_k - true_positives

    precision_at_k = (
        true_positives / total_top_k
        if total_top_k > 0 else 0
    )

    total_actual_insiders = insiders[insider_user_col].nunique()

    detected_insiders = alerts[
        alerts["is_known_insider"]
    ][alert_user_col].nunique()

    false_negatives = total_actual_insiders - detected_insiders

    recall_at_k = (
        detected_insiders / total_actual_insiders
        if total_actual_insiders > 0 else 0
    )

    hit_rate_at_k = 1 if true_positives > 0 else 0

    # Print results
    print(f"Top K evaluated: {total_top_k}")
    print(f"True positives in Top K: {true_positives}")
    print(f"False positives in Top K: {false_positives}")
    print(f"Precision@K: {precision_at_k * 100:.2f}%")
    print(f"Recall@K: {recall_at_k * 100:.2f}%")
    print(f"False negatives: {false_negatives}")
    print(f"HitRate@K: {hit_rate_at_k}")

    print("\nUnique insider users detected in Top K:")
    print(detected_insiders)

    alerts.to_csv(output_csv, index=False)
    print(f"\nOutput saved to: {output_csv}")

    return alerts


if __name__ == "__main__":
    compared = compare_rule_alerts_with_insiders_top_k(
        alerts_csv=r"C:\Users\Hamed\Documents\python\projects\ueba\output\rule_alerts.csv",
        insiders_csv=r"C:\Users\Hamed\Documents\python\projects\ueba\r4.2\answers\insiders.csv",
        output_csv=r"C:\Users\Hamed\Documents\python\projects\ueba\output\evaluate_alerts_top_k.csv",
        k=2500
    )