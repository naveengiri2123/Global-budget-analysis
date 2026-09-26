import mysql.connector
import pandas as pd

def run_advanced_analytics():
    conn = mysql.connector.connect(
        host="localhost", user="root", password="Roots", database="global_budget_db"
    )
    cursor = conn.cursor()
    # 1. analysis: year-over-year (yoy) growth & 5-year rolling moving average 
    moving_avg_query = """
        select
            c.country_name, b.year, b.total_budget_billions_usd,
            avg(b.total_budget_billions_usd) over (
                partition by c.country_name
                order by b.year
                rows between 4 preceding and current row
            ) as rolling_5yr_avg
        from budgets b
        join countries c on b.country_id = c.country_id;
    """
    df_moving = pd.read_sql(moving_avg_query, conn)
    print("--- 1. 5-year rolling budget trends ---\n", df_moving.head())

    # 2. analysis: Historic sector dominance matrix (isolating the #1 funded sector per year)
    dominance_query = """
        with Rankedsector as (
            select
                c.country_name, b.year, sa.sector_name, sa.allocated_percentage,
                dense_rank() over (partition by c.country_name, b.year order by sa.allocated_percentage desc) as rnk
            from Sector_allocations sa
            join budgets b on sa.budget_id = b.budget_id
            join countries c on b.country_id = c.country_id
        )
        select country_name, year, sector_name, allocated_percentage
        from Rankedsector where rnk = 1;
    """

    df_dom = pd.read_sql(dominance_query, conn)
    print("\n--- 2. Historic #1 budget prirorities --- \n", df_dom.head())

    conn.close()

if __name__ == "__main__":
    run_advanced_analytics()
