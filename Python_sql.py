import pandas as pd
import mysql.connector
from mysql.connector import Error

def run_robust_etl(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(' ', '_')
    )

    required_columns = [
        'country',
        'year',
        'total_budget_billions_usd'
    ]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Missing required CSV columns: {missing_columns}")

    # handle any potential global missing data issue
    df = df.fillna(0)

    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Roots",
            database="global_budget_db",
            auth_plugin='mysql_native_password'
        )
        cursor = conn.cursor()

        print("🚀 step 1: seeding country dimension... ")
        unique_countries = df['country'].unique()
        for country in unique_countries:
            cursor.execute(
                "INSERT IGNORE INTO COUNTRIES (country_name) VALUES (%s)",
                (str(country).strip(),)
            )
            # Explicitly commit the dimension table first
            conn.commit()

        # Build an in-memory dictionary to look up ids instantly
        cursor.execute("SELECT country_name, country_id FROM countries")
        country_lookup = dict(cursor.fetchall())

        sectors = [
            'defense', 'education', 'health', 'interest_payments',
            'infrastructure', 'agriculture', 'state_transfers', 'social_welfare',
            'administration_and_others'
        ]

        print(f"🚀 step 2: ingesting {len(df)} fact records.....")
        success_count = 0

        for idx, row in df.iterrows():
            try:
                country_name = str(row['country']).strip()
                country_id = country_lookup[country_name]
                year = int(row['year'])
                total_budget = float(row['total_budget_billions_usd'])

                # Insert core budget header record
                cursor.execute(
                    """INSERT INTO budgets
                    (country_id, year, total_budget_billions_usd)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        budget_id = LAST_INSERT_ID(budget_id),
                        total_budget_billions_usd = VALUES(total_budget_billions_usd)""",
                    (country_id, year, total_budget)
                )
                budget_id = cursor.lastrowid

                # unpivot and map individual sector metrics
                for sector in sectors:
                    pct_col = f"{sector}_percentage"
                    amt_col = f"{sector}_amount_billions_usd"

                    cursor.execute(
                        """INSERT INTO sector_allocations
                        (budget_id, sector_name, allocated_percentage, allocated_amount_billions_usd)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            allocated_percentage = VALUES(allocated_percentage),
                            allocated_amount_billions_usd = VALUES(allocated_amount_billions_usd)""",
                        (budget_id, sector, float(row[pct_col]), float(row[amt_col]))
                    )
                success_count += 1

            except Error as row_err:
                print(f"⚠️ Error processing row {idx} ({country_name}-{year}): {row_err}")
                continue

        # CRITICAL: FINAL BLOCK SAVE VERIFICATION
        conn.commit()
        print(f"🏁 ETL complete! Successfully committed {success_count} structural records into MySQL")

    except Error as db_err:
        print(f"❌ structural database connection failure: {db_err}")

    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    run_robust_etl("Master_Global_Budgets_Historical.csv")