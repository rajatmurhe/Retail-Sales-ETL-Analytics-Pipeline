-- Star schema for the MySQL warehouse (load.py creates the same tables through SQLAlchemy).
-- Grain of fact_sales: one row per transaction.
CREATE DATABASE IF NOT EXISTS retail_db;
USE retail_db;

CREATE TABLE dim_customer (
    customer_id   VARCHAR(10) PRIMARY KEY,
    customer_name VARCHAR(50) NOT NULL,
    city          VARCHAR(30) NOT NULL
);

CREATE TABLE dim_product (
    product_id   VARCHAR(10) PRIMARY KEY,
    product_name VARCHAR(50) NOT NULL,
    category     VARCHAR(30) NOT NULL,
    price        DECIMAL(10, 2) NOT NULL,
    cost         DECIMAL(10, 2) NOT NULL
);

CREATE TABLE dim_date (
    date_id INT PRIMARY KEY,          -- YYYYMMDD
    date    DATE NOT NULL,
    year    INT NOT NULL,
    month   INT NOT NULL,
    day     INT NOT NULL
);

CREATE TABLE fact_sales (
    transaction_id VARCHAR(10) PRIMARY KEY,
    date_id        INT NOT NULL,
    customer_id    VARCHAR(10) NOT NULL,
    product_id     VARCHAR(10) NOT NULL,
    quantity       INT NOT NULL CHECK (quantity > 0),
    revenue        DECIMAL(12, 2) NOT NULL,
    profit         DECIMAL(12, 2) NOT NULL,
    FOREIGN KEY (date_id)     REFERENCES dim_date (date_id),
    FOREIGN KEY (customer_id) REFERENCES dim_customer (customer_id),
    FOREIGN KEY (product_id)  REFERENCES dim_product (product_id)
);
