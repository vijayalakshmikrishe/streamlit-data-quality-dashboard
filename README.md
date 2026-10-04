# Streamlit Data Quality & Pipeline Health Dashboard

An operational dashboard giving engineering and business stakeholders
visibility into pipeline execution, data freshness, and data quality --
the same purpose served by production Streamlit dashboards built on
Snowflake Information Schema and Account Usage views.

## What it shows

- **Top-line KPIs**: pipelines monitored, latest success rate, flagged
  issues today, total runs in the last 30 days
- **Daily success rate per pipeline**, as a trend line, so a degrading
  pipeline is visible before it becomes a full outage
- **Flagged runs table**: every run that either failed outright, or
  "succeeded" but loaded zero rows -- a common silent-failure pattern
  that a status code alone won't catch
- **Row volume over time**, to catch unusual drops in data volume even
  when a pipeline technically reports success

## Why "succeeded with 0 rows" is treated as an issue

A pipeline that completes without error but loads no data is often a
worse problem than an outright failure, because it doesn't trigger
alerts on its own. This dashboard applies the same filter logic used in
the Python ETL framework's data quality checks: flag on
`status == 'fail' OR rows_loaded == 0`, not just on failure status
alone.

## Running it

```
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`. Uses mock data in `mock_data/` so it
runs standalone -- no live Snowflake connection required to try it.

## Connecting it to a real pipeline

To point this at a live platform instead of mock data, replace
`load_data()` in `app.py` with a query against a Snowflake control table
populated by the pipelines in `snowflake-end-to-end-pipeline`, using
`snowflake-connector-python` or `snowflake-snowpark-python`. The rest of
the dashboard logic is unchanged.

## How this fits a larger platform

This dashboard is the visibility layer for the other three repos in this
portfolio: it surfaces results from the data quality checks defined in
`python-etl-metadata-framework`, monitors the pipelines orchestrated in
`snowflake-end-to-end-pipeline`, and reports on the dimensional models
built in `subscription-analytics-dbt-snowflake`.
