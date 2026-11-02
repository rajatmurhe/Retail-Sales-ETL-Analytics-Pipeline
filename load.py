"""Load step: creates the star schema with primary and foreign keys, then loads data/processed/*.csv.

The connection string comes from the RETAIL_DB_URL environment variable (never hardcode passwords):
    MySQL : export RETAIL_DB_URL="mysql+pymysql://<user>:<password>@localhost/retail_db"
    Local : defaults to SQLite (retail_dw.db) so the pipeline runs with no database server.

Each run is a full refresh: tables are dropped and recreated, so rerunning gives the same result.
"""
import os

import pandas as pd
from sqlalchemy import (Column, Date, ForeignKey, Integer, MetaData, Numeric, String, Table,
                        create_engine)

DB_URL = os.environ.get("RETAIL_DB_URL", "sqlite:///retail_dw.db")
IN_DIR = os.path.join("data", "processed")

metadata = MetaData()
dim_customer = Table("dim_customer", metadata,
                     Column("customer_id", String(10), primary_key=True),
                     Column("customer_name", String(50), nullable=False),
                     Column("city", String(30), nullable=False))
dim_product = Table("dim_product", metadata,
                    Column("product_id", String(10), primary_key=True),
                    Column("product_name", String(50), nullable=False),
                    Column("category", String(30), nullable=False),
                    Column("price", Numeric(10, 2), nullable=False),
                    Column("cost", Numeric(10, 2), nullable=False))
dim_date = Table("dim_date", metadata,
                 Column("date_id", Integer, primary_key=True),
                 Column("date", Date, nullable=False),
                 Column("year", Integer, nullable=False),
                 Column("month", Integer, nullable=False),
                 Column("day", Integer, nullable=False))
fact_sales = Table("fact_sales", metadata,
                   Column("transaction_id", String(10), primary_key=True),
                   Column("date_id", Integer, ForeignKey("dim_date.date_id"), nullable=False),
                   Column("customer_id", String(10), ForeignKey("dim_customer.customer_id"), nullable=False),
                   Column("product_id", String(10), ForeignKey("dim_product.product_id"), nullable=False),
                   Column("quantity", Integer, nullable=False),
                   Column("revenue", Numeric(12, 2), nullable=False),
                   Column("profit", Numeric(12, 2), nullable=False))

LOAD_ORDER = [dim_customer, dim_product, dim_date, fact_sales]  # dimensions before the fact


def main(db_url: str = DB_URL):
    engine = create_engine(db_url)
    metadata.drop_all(engine)
    metadata.create_all(engine)
    with engine.begin() as conn:
        for table in LOAD_ORDER:
            df = pd.read_csv(os.path.join(IN_DIR, f"{table.name}.csv"))
            if table is dim_date:
                df["date"] = pd.to_datetime(df["date"]).dt.date
            conn.execute(table.insert(), df.to_dict(orient="records"))
            print(f"Loaded {len(df):>6} rows into {table.name}")


if __name__ == "__main__":
    main()
