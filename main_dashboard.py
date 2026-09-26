import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Global Budget analytics", layout="wide")


def get_engine():
    password_quoted = urllib.parse.quote_plus("Roots")
    return create_engine(
        f"mysql+pymysql://root:{password_quoted}@localhost/global_budget_db"
    )


def load_countries(engine):
    return pd.read_sql_query(
        "SELECT country_name FROM countries ORDER BY country_name",
        engine,
    )

def load_budget_trends(engine, country_name):
    query = """
        SELECT b.year, b.total_budget_billions_usd
        FROM budgets b
        JOIN countries c ON b.country_id = c.country_id
        WHERE c.country_name = %s
        ORDER BY b.year
    """
    return pd.read_sql_query(query, engine, params=(country_name,))


def load_sector_allocations(engine, country_name):
    query = """
        SELECT b.year,
               sa.sector_name,
               sa.allocated_percentage,
               sa.allocated_amount_billions_usd
        FROM sector_allocations sa
        JOIN budgets b ON sa.budget_id = b.budget_id
        JOIN countries c ON b.country_id = c.country_id
        WHERE c.country_name = %s
        ORDER BY b.year
    """
    return pd.read_sql_query(query, engine, params=(country_name,))


def load_correlation_data(engine, country_name):
    query = """
        SELECT b.year, sa.sector_name, sa.allocated_percentage
        FROM sector_allocations sa
        JOIN budgets b ON sa.budget_id = b.budget_id
        JOIN countries c ON b.country_id = c.country_id
        WHERE c.country_name = %s
        ORDER BY b.year
    """
    return pd.read_sql_query(query, engine, params=(country_name,))


def load_volatility_data(engine, country_name):
    query = """
        SELECT b.year, b.total_budget_billions_usd
        FROM budgets b
        JOIN countries c ON b.country_id = c.country_id
        WHERE c.country_name = %s
        ORDER BY b.year
    """
    return pd.read_sql_query(query, engine, params=(country_name,))


st.title(" 🏠 Global government budget analytics core ")
st.markdown(
    "An interactive platform exploring public finance shifts, sector dominance, and predictive trajectories."
)

engine = get_engine()
countries_df = load_countries(engine)
engine.dispose()

if countries_df.empty:
    st.warning("No countries available in the database.")
    st.stop()

selected_country = st.sidebar.selectbox(
    "Select a country",
    countries_df["country_name"].tolist(),
)


tab_marco, tab_sectors, tab_anomalies, tab_research_lab = st.tabs([
    "marco Historical trends",
    "sectors Sectoral spreads",
    "statistics Anomalies",
    "marco economic research lab",
])

with tab_marco:
    st.header("global spending growth pathways")
    engine = get_engine()
    df_marco = load_budget_trends(engine, selected_country)
    engine.dispose()

    if not df_marco.empty:
        fig_marco = px.line(
            df_marco,
            x="year",
            y="total_budget_billions_usd",
            title=f"historical expenditure strategy: {selected_country}",
            template="plotly_dark",
            labels={"total_budget_billions_usd": "Total Budget (Billions USD)"},
        )
        st.plotly_chart(fig_marco, width="stretch")
    else:
        st.info("No records found for the selected country.")

with tab_sectors:
    st.header("allocation distribution analysis")
    engine = get_engine()
    df_sectors = load_sector_allocations(engine, selected_country)
    engine.dispose()

    if not df_sectors.empty:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            fig_area = px.area(
                df_sectors,
                x="year",
                y="allocated_percentage",
                color="sector_name",
                title="structural budget shifts over time",
                template="plotly_dark",
            )
            st.plotly_chart(fig_area, width="stretch")

        with col_c2:
            fig_box = px.box(
                df_sectors,
                x="sector_name",
                y="allocated_percentage",
                color="sector_name",
                title="variance and spread across sectors",
                template="plotly_dark",
            )
            st.plotly_chart(fig_box, width="stretch")
    else:
        st.info("No sector records found for this country.")

with tab_anomalies:
    st.header("descriptive outliers detection")
    st.markdown(
        "Identifies fiscal years where spending shifted sharply outside normal historical baselines."
    )

    engine = get_engine()
    df_marco = load_budget_trends(engine, selected_country)
    engine.dispose()

    if df_marco.empty:
        st.info("No budget trend records available for anomaly detection.")
    else:
        mean_value = df_marco["total_budget_billions_usd"].mean()
        std_value = df_marco["total_budget_billions_usd"].std()
        df_marco["z_score"] = (
            df_marco["total_budget_billions_usd"] - mean_value
        ) / std_value
        anomalies = df_marco[df_marco["z_score"].abs() > 1.96]

        st.write("### flagged fiscal outlier periods (z-score > 1.96)")
        if not anomalies.empty:
            st.dataframe(
                anomalies.style.background_gradient(
                    cmap="Reds",
                    subset=["total_budget_billions_usd"],
                ),
                width="stretch",
            )
        else:
            st.success(
                "Excellent budget structural stability: no extreme statistical shifts and spending volatility."
            )

with tab_research_lab:
    st.header("⚠️ deep exploratory research lab")
    st.markdown(
        "Advanced analytics module calculating structural correlation shifts and spending volatility."
    )

    st.subheader("cross-sector allocation correlation matrix")
    engine = get_engine()
    df_corr_raw = load_correlation_data(engine, selected_country)
    engine.dispose()

    if not df_corr_raw.empty:
        pivot_df = df_corr_raw.pivot_table(
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
            labels={"color": "correlation coefficient"},
            template="plotly_dark",
        )
        st.plotly_chart(fig_heat, width="stretch")
    else:
        st.info("No sector allocation data available to compute correlations.")

    st.subheader("volatility index and rolling statistics")
    engine = get_engine()
    df_volatility = load_volatility_data(engine, selected_country)
    engine.dispose()

    if not df_volatility.empty:
        df_volatility = df_volatility.sort_values("year")
        df_volatility["rolling_mean"] = (
            df_volatility["total_budget_billions_usd"].rolling(window=10).mean()
        )
        df_volatility["rolling_std"] = (
            df_volatility["total_budget_billions_usd"].rolling(window=10).std()
        )
        df_volatility["volatility_index"] = (
            df_volatility["rolling_std"] / df_volatility["rolling_mean"] * 100
        )

        st.markdown("rolling 10-year volatility index (coefficient of variation)")
        fig_volatility = go.Figure()
        fig_volatility.add_trace(
            go.Scatter(
                x=df_volatility["year"],
                y=df_volatility["volatility_index"],
                mode="lines+markers",
                name="Volatility Index",
                line=dict(color="orange"),
            )
        )
        fig_volatility.update_layout(
            template="plotly_dark",
            yaxis_title="Volatility Index (%)",
        )
        st.plotly_chart(fig_volatility, width="stretch")

        st.write("recent rolling statistics (non-null rows):")
        st.dataframe(df_volatility.dropna().tail(10), width="stretch")
    else:
        st.info("Not enough historical data to compute volatility metrics for this country.")

    st.subheader("polynomial projection (analytical)")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        proj_degree = st.selectbox("projection degree", [1, 2, 3], index=1)
        proj_horizon = st.number_input(
            "forecast horizon year",
            min_value=2025,
            max_value=2050,
            value=2035,
        )
    with col_p2:
        apply_scenario = st.checkbox("apply scenario shock to projection")
        shock_pct = st.slider("shock %", -50, 100, 0)

    if not df_volatility.empty:
        x = df_volatility["year"].astype(int).values
        y = df_volatility["total_budget_billions_usd"].astype(float).values

        if len(x) > proj_degree:
            coeffs = np.polyfit(x, y, deg=proj_degree)
            poly = np.poly1d(coeffs)
            years_future = np.arange(int(x.max()) + 1, int(proj_horizon) + 1)
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
                    marker=dict(color="#888888"),
                )
            )
            fig_proj.add_trace(
                go.Scatter(
                    x=years_future,
                    y=proj_vals,
                    mode="lines",
                    name="Projection",
                    line=dict(color="#0ffaa0", dash="dash"),
                )
            )
            fig_proj.update_layout(
                title=f"polynomial projection (deg {proj_degree}) for {selected_country}",
                template="plotly_dark",
                xaxis_title="year",
                yaxis_title="Budget (billions USD)",
            )
            st.plotly_chart(fig_proj, width="stretch")

            df_proj_out = pd.DataFrame(
                {
                    "year": years_future,
                    "projected_budget": proj_vals,
                }
            )
            st.dataframe(
                df_proj_out.style.format({"projected_budget": "${:,.2f}"}),
                width="stretch",
            )
        else:
            st.warning("Not enough historical points for the selected polynomial degree.")
