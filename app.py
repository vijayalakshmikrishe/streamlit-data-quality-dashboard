"""
Pipeline Health & Data Quality Dashboard

A Streamlit app giving engineering and business stakeholders visibility
into pipeline execution, data freshness, and data quality -- the same
purpose served by production dashboards built on Snowflake Information
Schema and Account Usage views, surfacing pipeline health, ingestion
status, and operational KPIs.

In production, `load_data()` below would query Snowflake directly
(e.g. a control table populated by the stored procedures in the
python-etl-metadata-framework repo). Here it reads a mock CSV so the
dashboard runs standalone with no live warehouse required.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Pipeline Health Dashboard", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv("mock_data/pipeline_runs.csv", parse_dates=["run_date"])
    return df


def flag_issues(df: pd.DataFrame) -> pd.DataFrame:
    """Same logic as flag_issues() in the ETL framework: a pipeline run is
    flagged if it failed, OR if it 'succeeded' but loaded zero rows."""
    flagged = df[(df["status"] == "fail") | (df["rows_loaded"] == 0)]
    return flagged


def main():
    df = load_data()

    st.title("Pipeline Health & Data Quality Dashboard")
    st.caption("Operational visibility into ETL pipeline execution, freshness, and data quality.")

    # --- Top-line KPIs ---
    latest_date = df["run_date"].max()
    today_runs = df[df["run_date"] == latest_date]
    success_rate = (today_runs["status"] == "success").mean() * 100
    flagged_today = flag_issues(today_runs)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Pipelines monitored", df["pipeline_name"].nunique())
    col2.metric("Success rate (latest run)", f"{success_rate:.0f}%")
    col3.metric("Flagged issues (latest run)", len(flagged_today))
    col4.metric("Total runs (30 days)", len(df))

    st.divider()

    # --- Success rate over time, per pipeline ---
    st.subheader("Daily success rate by pipeline")
    daily = (
        df.groupby(["run_date", "pipeline_name"])["status"]
        .apply(lambda s: (s == "success").mean() * 100)
        .reset_index(name="success_rate_pct")
    )
    chart = (
        alt.Chart(daily)
        .mark_line(point=True)
        .encode(
            x="run_date:T",
            y=alt.Y("success_rate_pct:Q", title="Success rate (%)", scale=alt.Scale(domain=[0, 100])),
            color="pipeline_name:N",
            tooltip=["run_date:T", "pipeline_name:N", "success_rate_pct:Q"],
        )
        .properties(height=350)
    )
    st.altair_chart(chart, use_container_width=True)

    st.divider()

    # --- Flagged runs table (fail OR succeeded-with-zero-rows) ---
    st.subheader("Flagged runs (failed, or succeeded with 0 rows loaded)")
    all_flagged = flag_issues(df).sort_values("run_date", ascending=False)
    st.dataframe(
        all_flagged[["run_date", "pipeline_name", "status", "rows_loaded", "duration_seconds"]],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # --- Row volume trend ---
    st.subheader("Rows loaded per pipeline over time")
    volume = df[df["status"] == "success"]
    vol_chart = (
        alt.Chart(volume)
        .mark_bar()
        .encode(
            x="run_date:T",
            y=alt.Y("rows_loaded:Q", title="Rows loaded"),
            color="pipeline_name:N",
            tooltip=["run_date:T", "pipeline_name:N", "rows_loaded:Q"],
        )
        .properties(height=300)
    )
    st.altair_chart(vol_chart, use_container_width=True)


if __name__ == "__main__":
    main()
