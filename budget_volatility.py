from sqlalchemy import create_engine
import pandas as pd


def analyze_budget_volatility(country_name):
    engine = create_engine(
        "mysql+pymysql://root:Roots@localhost/global_budget_db"
    )

    # Extract historical spending sequence
    query = """
        SELECT
            b.year,
            b.total_budget_billions_usd
        FROM budgets b
        JOIN countries c
            ON b.country_id = c.country_id
        WHERE c.country_name = %s
        ORDER BY b.year ASC;
    """

    df = pd.read_sql_query(
        query,
        engine,
        params=(country_name,)
    )

    if df.empty:
        print(f"No budget data found for {country_name}")
        return

    # Calculate 10-year rolling mean
    df["rolling_mean"] = (
        df["total_budget_billions_usd"]
        .rolling(window=10)
        .mean()
    )

    # Calculate 10-year rolling standard deviation
    df["rolling_std"] = (
        df["total_budget_billions_usd"]
        .rolling(window=10)
        .std()
    )

    # Calculate volatility index
    # Coefficient of variation = standard deviation / mean × 100
    df["volatility_index"] = (
        df["rolling_std"] / df["rolling_mean"]
    ) * 100

    print(
        f"\n--- Budget volatility index for {country_name} ---"
    )

    print(
        df.dropna().head(10)
    )

    return df


if __name__ == "__main__":
    analyze_budget_volatility("India")
