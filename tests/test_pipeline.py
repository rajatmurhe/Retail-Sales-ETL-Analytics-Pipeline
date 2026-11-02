"""Unit and end to end tests for the Retail Sales ETL pipeline (run with: pytest -q)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pipeline  # noqa: E402


def test_extract_is_reproducible():
    a = pipeline.extract(seed=7, n=500)
    b = pipeline.extract(seed=7, n=500)
    assert a.equals(b)
    assert len(a) == 500


def test_cleaning_removes_injected_problems():
    raw = pipeline.inject_issues(pipeline.extract(n=2000))
    tables, quarantine, summary = pipeline.transform(raw)
    fact = tables["fact_sales"]
    assert summary["duplicates_removed"] == 20          # 1% of 2,000 rows were duplicated
    assert (fact["quantity"] > 0).all()
    assert fact["transaction_id"].is_unique
    assert summary["raw_rows"] == summary["duplicates_removed"] + summary["quarantined_rows"] + summary["fact_rows"]
    assert set(quarantine["reason"]) <= {"quantity <= 0", "missing required field"}


def test_star_schema_keys_join():
    tables, _, _ = pipeline.transform(pipeline.inject_issues(pipeline.extract(n=1000)))
    fact = tables["fact_sales"]
    assert set(fact["customer_id"]) <= set(tables["dim_customer"]["customer_id"])
    assert set(fact["product_id"]) <= set(tables["dim_product"]["product_id"])
    assert set(fact["date_id"]) <= set(tables["dim_date"]["date_id"])


def test_end_to_end_sqlite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    import load, validate, run_analytics  # noqa: E401
    pipeline.main()
    db = f"sqlite:///{tmp_path / 'test.db'}"
    load.main(db)
    assert validate.main(db) == 0
    monkeypatch.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert run_analytics.main(db) == 18
