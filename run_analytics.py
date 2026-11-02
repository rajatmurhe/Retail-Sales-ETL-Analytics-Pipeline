"""Runs every query in analytics.sql against the warehouse and prints a short preview of each result."""
import os
import re

import pandas as pd
from sqlalchemy import create_engine, text

DB_URL = os.environ.get("RETAIL_DB_URL", "sqlite:///retail_dw.db")


def queries(path: str = "analytics.sql"):
    sql = open(path).read()
    for block in re.split(r"\n(?=-- \d+\.)", sql):
        title = re.search(r"-- (\d+\..*)", block)
        body = "\n".join(l for l in block.splitlines() if not l.strip().startswith("--")).strip().rstrip(";")
        if title and body:
            yield title.group(1), body


def main(db_url: str = DB_URL) -> int:
    engine = create_engine(db_url)
    count = 0
    with engine.connect() as conn:
        for title, body in queries():
            df = pd.read_sql(text(body), conn)
            count += 1
            print(f"\n{title}\n{df.head(5).to_string(index=False)}")
    print(f"\nRan {count} queries.")
    return count


if __name__ == "__main__":
    main()
