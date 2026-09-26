from sqlalchemy import create_engine
import pandas as pd
def compute_budget_correlations(country_name):
    engine = create_engine("mysql+pymysql://root:Roots@localhost/global_budget_db")

    # Query all sector percentage for a country over its entire history
    query = """
        SELECT b.year, sa.sector_name, sa.allocated_percentage
        FROM sector_allocations sa
        JOIN budgets b on sa.budget_id = b.budget_id
        JOIN countries c ON b.country_id = c.country_id
        WHERE c.country_name = %s;
    """
    df = pd.read_sql_query(query, engine, params=(country_name,))

    if df.empty:
        return

    # Pivot table from long form back to wide format to compute cross-correlation metrics
    wide_df = df.pivot(index='year', columns='sector_name', values='allocated_percentage')

    # calculate the pearson correlation matrix
    correlation_matrix = wide_df.corr()

    print(f"\n--- ⚠️ cross-sector correlation matrix for {country_name} ---")
    print(correlation_matrix.round(2))
    return correlation_matrix

if __name__ == "__main__":
    compute_budget_correlations("India")

