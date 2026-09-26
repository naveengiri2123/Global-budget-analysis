import os
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
import pandas as pd


def get_engine():
    database_url = os.getenv(
        "GLOBAL_BUDGET_DB_URL",
        "mysql+pymysql://root:Roots@localhost/global_budget_db",
    )
    return create_engine(database_url)


def analyze_guns_butter(selected_year=2025):
    query = """
        SELECT
            c.country_name,
            MAX(CASE
                WHEN LOWER(REPLACE(TRIM(sa.sector_name), '_', ' ')) = 'defense'
                THEN sa.allocated_percentage
            END) AS defense_percentage,
            MAX(CASE
                WHEN LOWER(REPLACE(TRIM(sa.sector_name), '_', ' ')) = 'social welfare'
                THEN sa.allocated_percentage
            END) AS social_welfare_percentage,
            MAX(CASE
                WHEN LOWER(REPLACE(TRIM(sa.sector_name), '_', ' ')) = 'education'
                THEN sa.allocated_percentage
            END) AS education_percentage
        FROM sector_allocations sa
        JOIN budgets b ON sa.budget_id = b.budget_id
        JOIN countries c ON b.country_id = c.country_id
        WHERE b.year = %s
        GROUP BY c.country_name;
    """

    engine = get_engine()
    try:
        # ✅ params को tuple में पास करें
        return pd.read_sql_query(query, engine, params=(selected_year,))
    except SQLAlchemyError as exc:
        print(f"Database error: {exc}")
        return pd.DataFrame()


if __name__ == "__main__":
    df = analyze_guns_butter(2025)
    if df.empty:
        print("No results returned.")
    else:
        print(df.to_string(index=False))
