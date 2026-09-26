import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="Global Budget Analytics",
    page_icon="🌍",
    layout="wide"
)

DATA_FILE = "Master_Global_Budgets_Historical.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_FILE)

    # Normalize column names used by the dashboard
    df["Country"] = df["Country"].astype(str).str.strip()
    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")

    numeric_cols = [c for c in df.columns if c not in ["Country"]]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=["Country", "Year"])


@st.cache_data
def load_sector_data(df, country_name):
    country_df = df[df["Country"] == country_name].copy()

    sector_map = {
        "Defense": "Defense_Percentage",
        "Education": "Education_Percentage",
        "Health": "Health_Percentage",
        "Interest Payments": "Interest_Payments_Percentage",
        "Infrastructure": "Infrastructure_Percentage",
        "Agriculture": "Agriculture_Percentage",
        "State Transfers": "State_Transfers_Percentage",
        "Social Welfare": "Social_Welfare_Percentage",
        "Administration & Others": "Administration_and_Others_Percentage",
    }

    rows = []
    for sector, column in sector_map.items():
        if column in country_df.columns:
            temp = country_df[["Year", column]].copy()
            temp["sector_name"] = sector
            temp["allocated_percentage"] = temp[column]
            rows.append(temp[["Year", "sector_name", "allocated_percentage"]])

    if not rows:
        return pd.DataFrame(
            columns=["year", "sector_name", "allocated_percentage"]
        )

    result = pd.concat(rows, ignore_index=True)
    result = result.rename(columns={"Year": "year"})
    return result.sort_values(["year", "sector_name"])


def load_budget_trends(df, country_name):
    result = df[df["Country"] == country_name][
        ["Year", "Total_Budget_Billions_USD"]
    ].copy()

    return result.rename(
        columns={
            "Year": "year",
            "Total_Budget_Billions_USD": "total_budget_billions_usd",
        }
    ).sort_values("year")


st.title("🌍 Global government budget analytics core")

st.markdown(
    "An interactive platform exploring public finance shifts, "
    "sector dominance, anomalies, volatility, and predictive trajectories."
)

# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------
try:
    df = load_data()
except FileNotFoundError:
    st.error(
        f"Dataset not found: {DATA_FILE}. "
        "Make sure the CSV is in the same folder as main_dashboard.py."
    )
    st.stop()
except Exception as e:
    st.error("Unable to load the budget dataset.")
    st.exception(e)
    st.stop()

if df.empty:
    st.warning("No budget records are available.")
    st.stop()

countries = sorted(df["Country"].dropna().unique().tolist())

selected_country = st.sidebar.selectbox(
    "Select a country",
    countries
)

country_df = df[df["Country"] == selected_country].copy()

tab_marco, tab_sectors, tab_anomalies, tab_research_lab = st.tabs([
    "📈 Historical trends",
    "📊 Sectoral spreads",
    "📉 Anomalies",
    "🔬 Economic research lab",
])

# =========================================================
# TAB 1: HISTORICAL TRENDS
# =========================================================
with tab_marco:
    st.header("Global spending growth pathways")

    df_marco = load_budget_trends(df, selected_country)

    if not df_marco.empty:
        fig_marco = px.line(
            df_marco,
            x="year",
            y="total_budget_billions_usd",
            title=f"Historical expenditure strategy: {selected_country}",
            template="plotly_dark",
            labels={
                "year": "Year",
                "total_budget_billions_usd": "Total Budget (Billions USD)",
            },
        )
        st.plotly_chart(fig_marco, width="stretch")

        latest = df_marco.iloc[-1]
        first = df_marco.iloc[0]

        c1, c2, c3 = st.columns(3)
        c1.metric("Latest Budget", f"${latest['total_budget_billions_usd']:,.2f}B")
        c2.metric("Latest Year", int(latest["year"]))
        c3.metric(
            "Change Since First Year",
            f"{latest['total_budget_billions_usd'] - first['total_budget_billions_usd']:+,.2f}B"
        )
    else:
        st.info("No records found for the selected country.")

# =========================================================
# TAB 2: SECTORAL ANALYSIS
# =========================================================
with tab_sectors:
    st.header("Allocation distribution analysis")

    df_sectors = load_sector_data(df, selected_country)

    if not df_sectors.empty:
        col_c1, col_c2 = st.columns(2)

        with col_c1:
            fig_area = px.area(
                df_sectors,
                x="year",
                y="allocated_percentage",
                color="sector_name",
                title="Structural budget shifts over time",
                template="plotly_dark",
                labels={
                    "year": "Year",
                    "allocated_percentage": "Allocation (%)",
                    "sector_name": "Sector",
                },
            )
            st.plotly_chart(fig_area, width="stretch")

        with col_c2:
            fig_box = px.box(
                df_sectors,
                x="sector_name",
                y="allocated_percentage",
                color="sector_name",
                title="Variance and spread across sectors",
                template="plotly_dark",
                labels={
                    "sector_name": "Sector",
                    "allocated_percentage": "Allocation (%)",
                },
            )
            st.plotly_chart(fig_box, width="stretch")

        latest_year = int(df_sectors["year"].max())
        latest_sector = df_sectors[df_sectors["year"] == latest_year].copy()

        st.subheader(f"Sector allocation in {latest_year}")
        latest_sector = latest_sector.sort_values(
            "allocated_percentage", ascending=False
        )
        st.dataframe(
            latest_sector[
                ["sector_name", "allocated_percentage"]
            ].rename(
                columns={
                    "sector_name": "Sector",
                    "allocated_percentage": "Allocation (%)",
                }
            ),
            width="stretch",
        )
    else:
        st.info("No sector allocation records found for this country.")

# =========================================================
# TAB 3: ANOMALY DETECTION
# =========================================================
with tab_anomalies:
    st.header("Descriptive outlier detection")

    st.markdown(
        "Identifies fiscal years where total spending moved sharply "
        "outside the country's historical baseline."
    )

    df_marco = load_budget_trends(df, selected_country)

    if df_marco.empty:
        st.info("No budget trend records available for anomaly detection.")
    else:
        mean_value = df_marco["total_budget_billions_usd"].mean()
        std_value = df_marco["total_budget_billions_usd"].std()

        if pd.isna(std_value) or std_value == 0:
            st.info("Not enough variation to calculate statistical outliers.")
        else:
            df_marco = df_marco.copy()
            df_marco["z_score"] = (
                df_marco["total_budget_billions_usd"] - mean_value
            ) / std_value

            anomalies = df_marco[df_marco["z_score"].abs() > 1.96].copy()

            st.write("### Flagged fiscal outlier periods (|z-score| > 1.96)")

            if not anomalies.empty:
                st.dataframe(
                    anomalies[
                        ["year", "total_budget_billions_usd", "z_score"]
                    ].sort_values("year"),
                    width="stretch",
                )
            else:
                st.success(
                    "No extreme statistical shifts were detected "
                    "using the selected threshold."
                )

# =========================================================
# TAB 4: RESEARCH LAB
# =========================================================
with tab_research_lab:
    st.header("🔬 Deep exploratory research lab")

    st.markdown(
        "Advanced analytics for sector correlations, spending volatility, "
        "and polynomial projections."
    )

    # -----------------------------------------------------
    # Correlation matrix
    # -----------------------------------------------------
    st.subheader("Cross-sector allocation correlation matrix")

    df_corr = load_sector_data(df, selected_country)

    if not df_corr.empty:
        pivot_df = df_corr.pivot_table(
            index="year",
            columns="sector_name",
            values="allocated_percentage",
            aggfunc="mean",
        )

        corr_matrix = pivot_df.corr()

        fig_heat = px.imshow(
            corr_matrix,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            labels={"color": "Correlation coefficient"},
            title="Sector allocation correlations",
            template="plotly_dark",
        )
        st.plotly_chart(fig_heat, width="stretch")
    else:
        st.info("No sector allocation data available for correlations.")

    # -----------------------------------------------------
    # Volatility
    # -----------------------------------------------------
    st.subheader("Volatility index and rolling statistics")

    df_volatility = load_budget_trends(df, selected_country)

    if not df_volatility.empty:
        df_volatility = df_volatility.sort_values("year").copy()

        window = min(10, len(df_volatility))

        if window >= 2:
            df_volatility["rolling_mean"] = (
                df_volatility["total_budget_billions_usd"]
                .rolling(window=window)
                .mean()
            )

            df_volatility["rolling_std"] = (
                df_volatility["total_budget_billions_usd"]
                .rolling(window=window)
                .std()
            )

            df_volatility["volatility_index"] = (
                df_volatility["rolling_std"]
                / df_volatility["rolling_mean"]
                * 100
            )

            st.markdown(
                f"Rolling {window}-year volatility index "
                "(coefficient of variation)"
            )

            fig_volatility = go.Figure()

            fig_volatility.add_trace(
                go.Scatter(
                    x=df_volatility["year"],
                    y=df_volatility["volatility_index"],
                    mode="lines+markers",
                    name="Volatility Index",
                )
            )

            fig_volatility.update_layout(
                template="plotly_dark",
                yaxis_title="Volatility Index (%)",
                xaxis_title="Year",
            )

            st.plotly_chart(fig_volatility, width="stretch")

            st.write("Recent rolling statistics:")
            st.dataframe(
                df_volatility.dropna().tail(10),
                width="stretch",
            )
        else:
            st.info("Not enough historical data for volatility metrics.")
    else:
        st.info("No budget data available for volatility analysis.")

    # -----------------------------------------------------
    # Polynomial projection
    # -----------------------------------------------------
    st.subheader("Polynomial projection (analytical)")

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        proj_degree = st.selectbox(
            "Projection degree",
            [1, 2, 3],
            index=1,
        )

        min_year = int(df_volatility["year"].min())
        max_year = int(df_volatility["year"].max())

        proj_horizon = st.number_input(
            "Forecast horizon year",
            min_value=max(max_year + 1, 2025),
            max_value=2050,
            value=min(max(max_year + 10, 2035), 2050),
        )

    with col_p2:
        apply_scenario = st.checkbox("Apply scenario shock to projection")
        shock_pct = st.slider("Shock %", -50, 100, 0)

    if not df_volatility.empty:
        x = df_volatility["year"].astype(int).values
        y = df_volatility["total_budget_billions_usd"].astype(float).values

        if len(x) > proj_degree:
            coeffs = np.polyfit(x, y, deg=proj_degree)
            poly = np.poly1d(coeffs)

            years_future = np.arange(
                int(x.max()) + 1,
                int(proj_horizon) + 1,
            )

            proj_vals = poly(years_future)

            if apply_scenario and shock_pct != 0:
                proj_vals = proj_vals * (1 + shock_pct / 100.0)

            fig_proj = go.Figure()

            fig_proj.add_trace(
                go.Scatter(
                    x=x,
                    y=y,
                    mode="lines+markers",
                    name="Historical",
                )
            )

            fig_proj.add_trace(
                go.Scatter(
                    x=years_future,
                    y=proj_vals,
                    mode="lines",
                    name="Projection",
                    line=dict(dash="dash"),
                )
            )

            fig_proj.update_layout(
                title=(
                    f"Polynomial projection (degree {proj_degree}) "
                    f"for {selected_country}"
                ),
                template="plotly_dark",
                xaxis_title="Year",
                yaxis_title="Budget (Billions USD)",
            )

            st.plotly_chart(fig_proj, width="stretch")

            df_proj_out = pd.DataFrame(
                {
                    "year": years_future,
                    "projected_budget": proj_vals,
                }
            )

            st.dataframe(
                df_proj_out.style.format(
                    {"projected_budget": "${:,.2f}"}
                ),
                width="stretch",
            )
        else:
            st.warning(
                "Not enough historical points for the selected "
                "polynomial degree."
            )
