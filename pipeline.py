"""Extract and transform step of the Retail Sales ETL pipeline.

The source data is SYNTHETIC: we generate 12,000 retail transactions with a fixed seed,
then inject a small, controlled share of realistic data problems (duplicate rows, missing
values, invalid quantities) so the cleaning step has real work to do and can be measured.

Outputs (data/processed/):
    fact_sales.csv, dim_customer.csv, dim_product.csv, dim_date.csv  -> loaded by load.py
    quarantine.csv                                                   -> rows rejected by cleaning
    run_summary.json                                                 -> row counts for this run
"""
import json
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

SEED = 42
N_TRANSACTIONS = 12_000
N_CUSTOMERS = 500
OUT_DIR = os.path.join("data", "processed")

PRODUCTS = {
    "P01": ("Laptop", "Electronics", 800, 600),
    "P02": ("Mouse", "Electronics", 25, 10),
    "P03": ("Desk", "Furniture", 150, 80),
    "P04": ("Chair", "Furniture", 100, 50),
    "P05": ("Pen", "Office Supplies", 5, 1),
}
CITIES = ["Mumbai", "Delhi", "Bangalore", "Chennai", "Pune"]


def extract(seed: int = SEED, n: int = N_TRANSACTIONS) -> pd.DataFrame:
    """Generate the raw synthetic transactions. Seeds BOTH random and numpy, so runs are reproducible."""
    random.seed(seed)
    np.random.seed(seed)
    customers = [
        {"customer_id": f"C{i:04d}", "customer_name": f"Customer_{i}", "city": random.choice(CITIES)}
        for i in range(1, N_CUSTOMERS + 1)
    ]
    start = datetime(2023, 1, 1)
    rows = []
    for i in range(1, n + 1):
        pid = random.choice(list(PRODUCTS))
        cust = random.choice(customers)
        rows.append({
            "transaction_id": f"T{i:05d}",
            "date": (start + timedelta(days=random.randint(0, 364))).strftime("%Y-%m-%d"),
            "customer_id": cust["customer_id"],
            "customer_name": cust["customer_name"],
            "city": cust["city"],
            "product_id": pid,
            "product_name": PRODUCTS[pid][0],
            "category": PRODUCTS[pid][1],
            "price": PRODUCTS[pid][2],
            "cost": PRODUCTS[pid][3],
            "quantity": random.randint(1, 5),
        })
    return pd.DataFrame(rows)


def inject_issues(df: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    """Add realistic problems at fixed rates: 1% duplicate rows, 0.5% missing city, 0.3% bad quantity."""
    rng = np.random.default_rng(seed)
    df = df.copy()
    dupes = df.sample(frac=0.01, random_state=seed)
    missing = rng.choice(df.index, size=int(len(df) * 0.005), replace=False)
    df.loc[missing, "city"] = None
    bad = rng.choice(df.index.difference(missing), size=int(len(df) * 0.003), replace=False)
    df.loc[bad, "quantity"] = rng.choice([0, -1, -2], size=len(bad))
    return pd.concat([df, dupes], ignore_index=True)


def transform(raw: pd.DataFrame):
    """Clean the raw rows and split them into a star schema. Returns (tables, quarantine, summary)."""
    summary = {"raw_rows": len(raw)}
    df = raw.drop_duplicates()
    summary["duplicates_removed"] = summary["raw_rows"] - len(df)

    bad_qty = df["quantity"] <= 0
    missing = df[["transaction_id", "customer_id", "product_id", "date", "city"]].isna().any(axis=1)
    quarantine = df[bad_qty | missing].copy()
    quarantine["reason"] = np.where(bad_qty[bad_qty | missing], "quantity <= 0", "missing required field")
    df = df[~(bad_qty | missing)].copy()
    summary["quarantined_rows"] = len(quarantine)

    df["quantity"] = df["quantity"].astype(int)
    df["revenue"] = df["price"] * df["quantity"]
    df["profit"] = df["revenue"] - df["cost"] * df["quantity"]
    df["date"] = pd.to_datetime(df["date"])
    df["date_id"] = df["date"].dt.strftime("%Y%m%d").astype(int)

    dim_customer = df[["customer_id", "customer_name", "city"]].drop_duplicates("customer_id").sort_values("customer_id")
    dim_product = df[["product_id", "product_name", "category", "price", "cost"]].drop_duplicates("product_id").sort_values("product_id")
    dim_date = (df[["date_id", "date"]].drop_duplicates("date_id").sort_values("date_id").assign(
        year=lambda d: d["date"].dt.year, month=lambda d: d["date"].dt.month, day=lambda d: d["date"].dt.day))
    dim_date["date"] = dim_date["date"].dt.strftime("%Y-%m-%d")
    # Grain of fact_sales: one row per transaction (one product line per transaction).
    fact_sales = df[["transaction_id", "date_id", "customer_id", "product_id", "quantity", "revenue", "profit"]].sort_values("transaction_id")

    summary["fact_rows"] = len(fact_sales)
    tables = {"fact_sales": fact_sales, "dim_customer": dim_customer, "dim_product": dim_product, "dim_date": dim_date}
    return tables, quarantine, summary


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("Extract: generating synthetic transactions...")
    raw = inject_issues(extract())
    print("Transform: cleaning and building the star schema...")
    tables, quarantine, summary = transform(raw)
    for name, frame in tables.items():
        frame.to_csv(os.path.join(OUT_DIR, f"{name}.csv"), index=False)
    quarantine.to_csv(os.path.join(OUT_DIR, "quarantine.csv"), index=False)
    with open(os.path.join(OUT_DIR, "run_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
