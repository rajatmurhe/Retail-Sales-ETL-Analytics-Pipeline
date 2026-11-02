"""Data quality checks on the loaded warehouse. Exits with code 1 if any check fails.

Checks: row counts match the processed CSVs, primary keys are unique and not null,
every fact row joins to all three dimensions, quantities are positive, and
revenue equals price x quantity for every row.
"""
import os
import sys

import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = os.environ.get("RETAIL_DB_URL", "sqlite:///retail_dw.db")
IN_DIR = os.path.join("data", "processed")

CHECKS = {
    "fact_sales has no duplicate transaction_id":
        "SELECT COUNT(*) FROM (SELECT transaction_id FROM fact_sales GROUP BY transaction_id HAVING COUNT(*) > 1) d",
    "no null keys in fact_sales":
        "SELECT COUNT(*) FROM fact_sales WHERE transaction_id IS NULL OR date_id IS NULL OR customer_id IS NULL OR product_id IS NULL",
    "every fact row has a customer":
        "SELECT COUNT(*) FROM fact_sales f LEFT JOIN dim_customer c ON f.customer_id = c.customer_id WHERE c.customer_id IS NULL",
    "every fact row has a product":
        "SELECT COUNT(*) FROM fact_sales f LEFT JOIN dim_product p ON f.product_id = p.product_id WHERE p.product_id IS NULL",
    "every fact row has a date":
        "SELECT COUNT(*) FROM fact_sales f LEFT JOIN dim_date d ON f.date_id = d.date_id WHERE d.date_id IS NULL",
    "quantity is positive":
        "SELECT COUNT(*) FROM fact_sales WHERE quantity <= 0",
    "revenue equals price x quantity":
        "SELECT COUNT(*) FROM fact_sales f JOIN dim_product p ON f.product_id = p.product_id "
        "WHERE ABS(f.revenue - p.price * f.quantity) > 0.01",
}


def main(db_url: str = DB_URL) -> int:
    engine = create_engine(db_url)
    failures = 0
    with engine.connect() as conn:
        for table in ["fact_sales", "dim_customer", "dim_product", "dim_date"]:
            expected = len(pd.read_csv(os.path.join(IN_DIR, f"{table}.csv")))
            actual = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            ok = expected == actual
            failures += not ok
            print(f"[{'PASS' if ok else 'FAIL'}] {table} row count {actual} (expected {expected})")
        for name, sql in CHECKS.items():
            bad = conn.execute(text(sql)).scalar()
            failures += bad > 0
            print(f"[{'PASS' if bad == 0 else 'FAIL'}] {name} ({bad} bad rows)")
    print(f"\n{len(CHECKS) + 4 - failures} of {len(CHECKS) + 4} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
