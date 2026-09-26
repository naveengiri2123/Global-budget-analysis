import sys
import urllib.parse

import pandas as pd
from sqlalchemy import create_engine


def detect_budget_anomalies(country_name):
    host = "localhost"
    user = "root"
    password = "Roots"
    database = "global_budget_db"
    password_quoted = urllib.parse.quote_plus(password)
    
    engine = create_engine(
        f"mysql+mysqlconnector://{user}:{password_quoted}@{host}/{database}"
    ) 

    # extract complete sequence for the country
    query = """
         SELECT b.year, b.total_budget_billions_usd
         FROM budgets b
         JOIN countries c ON b.country_id = c.country_id
         WHERE c.country_name = %s
         ORDER BY b.year ASC
    """
    df = pd.read_sql_query(query, engine, params=(country_name,))
    engine.dispose()

    if df.empty:
        print(f"No budget data found for {country_name}.")
        return None

    # statistical analysis calculations
    mean_val = df['total_budget_billions_usd'].mean()
    std_dev = df['total_budget_billions_usd'].std()

    # calculate rolling z-score to flag shifts out of historical baselines
    df['z_score'] = (df['total_budget_billions_usd'] - mean_val) / std_dev

    # identify anomaly years where spending jumps outside a 95% confidence threshold (> 1.96 standard deviations)
    anomalies = df[df['z_score'].abs() > 1.96]

    print(f"\n--- flagged fiscal anomalies for {country_name} (outliers variance analysis) ---")
    if anomalies.empty:
        print("No extreme statistical outliers identified.")
        return None
    else:
        print(anomalies)
        return anomalies


if __name__ == "__main__":
    country_name = sys.argv[1] if len(sys.argv) > 1 else input("Enter country name: ").strip()
    detect_budget_anomalies(country_name)
