# Retail Sales ETL and Analytics Pipeline

A batch ETL pipeline in Python that cleans retail transactions, loads them into a star schema warehouse (MySQL, or SQLite for local runs), validates the load with data quality checks, and answers business questions with 18 SQL queries and a Power BI dashboard.

**Data is synthetic.** The extract step generates 12,000 transactions with a fixed seed, then injects a controlled share of realistic problems so cleaning has measurable work to do.

### Power BI dashboard
![Power BI Dashboard](screenshots/dashboard.png)

### SQL results
![SQL Query Results](screenshots/sql_results.png)

*Both screenshots come from an earlier run of the pipeline, before the seeded and validated version below.*

## Pipeline

| Step | Script | What it does |
| --- | --- | --- |
| Extract | `pipeline.py` | Generates 12,000 seeded transactions (500 customers, 5 products, 2023), then injects 1% duplicate rows, 0.5% missing cities and 0.3% invalid quantities |
| Transform | `pipeline.py` | Removes duplicates, sends invalid rows to `quarantine.csv` with a reason, computes revenue and profit, and splits the data into a star schema |
| Load | `load.py` | Creates the tables with primary and foreign keys, then loads dimensions before the fact table. Full refresh, so reruns give the same result |
| Validate | `validate.py` | 11 data quality checks: row counts, unique and non null keys, referential integrity, positive quantities, revenue = price x quantity |
| Analyse | `analytics.sql`, `run_analytics.py` | 18 queries, including a running total (`SUM OVER`), month over month growth (`LAG`) and top customers per city (`RANK`) |

### Results of a run (seed 42)

| Metric | Value |
| --- | --- |
| Raw rows (with injected problems) | 12,120 |
| Duplicates removed | 120 |
| Rows quarantined | 96 |
| Rows in `fact_sales` | 11,904 |
| Data quality checks passed | 11 of 11 |
| Rerun gives identical output | Yes (same file checksums) |

## Star schema

Grain of `fact_sales`: one row per transaction.

- `fact_sales` (transaction_id PK; date_id, customer_id, product_id FKs; quantity, revenue, profit)
- `dim_customer` (customer_id PK, name, city)
- `dim_product` (product_id PK, name, category, price, cost)
- `dim_date` (date_id PK in YYYYMMDD, date, year, month, day)

The MySQL DDL is in `schema.sql`; `load.py` creates the same tables through SQLAlchemy so the pipeline also runs on SQLite.

## Run it

```bash
pip install -r requirements.txt
python pipeline.py      # writes data/processed/
python load.py          # SQLite by default (retail_dw.db)
python validate.py      # exits 1 if any check fails
python run_analytics.py
pytest -q               # unit tests + an end to end run
```

To load into MySQL, copy `.env.example`, set `RETAIL_DB_URL` (for example `mysql+pymysql://<user>:<password>@localhost/retail_db`) and export it before `load.py`. Credentials are never stored in the code.

GitHub Actions runs the tests and the full pipeline on every push.

## Repository layout

```text
pipeline.py        extract + transform (writes data/processed/, git ignored)
load.py            star schema DDL + load
validate.py        data quality checks
analytics.sql      18 analysis queries
run_analytics.py   runs every query
schema.sql         MySQL DDL
tests/             pytest suite
data/              snapshot CSVs from the earlier run used for the Power BI screenshot
                   (data.csv is the customer dimension)
```

## Tech stack

Python (Pandas, NumPy, SQLAlchemy), MySQL / SQLite, SQL (CTEs, window functions), Power BI, pytest, GitHub Actions.
