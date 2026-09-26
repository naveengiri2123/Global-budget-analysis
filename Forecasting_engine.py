import mysql.connector
import pandas as pd
import numpy as np


def generate_statistical_forecast(country_name, target_year=2035, degree=2):
    """
    Fits an n-degree polynomial trend line to historical data using NumPy
    and projects it to a future year.
    """
    conn = mysql.connector.connect(
        host="localhost", user="root", password="Roots", database="global_budget_db"
    )

    query = """
        SELECT b.year, b.total_budget_billions_usd
        FROM budgets b
        JOIN countries c ON b.country_id = c.country_id
        WHERE c.country_name = %s
        ORDER BY b.year ASC;
    """
    df = pd.read_sql(query, conn, params=(country_name,))
    conn.close()

    if df.empty:
        return None, None

    # Extract structural arrays
    x_hist = df["year"].values
    y_hist = df["total_budget_billions_usd"].values

    # Least-squares polynomial fit
    coefficients = np.polyfit(x_hist, y_hist, deg=degree)
    polynomial_model = np.poly1d(coefficients)

    # Generate the historical trend baseline fit
    df["trend_fit"] = polynomial_model(x_hist)

    # Extrapolate forecast timeline up to the target year
    forecast_years = np.arange(x_hist.max() + 1, target_year + 1)
    forecast_predictions = polynomial_model(forecast_years)

    df_forecast = pd.DataFrame({
        "year": forecast_years,
        "forecasted_budget": forecast_predictions,
    })

    print(f"\n--- ❤️ pure analytical projections for {country_name} ({x_hist.max() + 1} - {target_year}) ---")
    print(df_forecast.head(10))

    return df, df_forecast


if __name__ == "__main__":
    hist_fit, future_proj = generate_statistical_forecast("India", target_year=2035, degree=2)
    if hist_fit is None:
        print("No historical data found for the requested country.")
    else:
        print("\nHistorical fit sample:")
        print(hist_fit.head())
