-- Retail Sales analytics: 18 queries over the star schema.
-- Runs on MySQL 8+ (run `USE retail_db;` first) and on SQLite 3.25+ (window functions).
-- Grain of fact_sales: one row per transaction.

-- 1. Total revenue
SELECT SUM(revenue) AS total_revenue FROM fact_sales;

-- 2. Total transactions
SELECT COUNT(*) AS total_transactions FROM fact_sales;

-- 3. Total units sold
SELECT SUM(quantity) AS total_units_sold FROM fact_sales;

-- 4. Total profit
SELECT SUM(profit) AS total_profit FROM fact_sales;

-- 5. Average order value (revenue per transaction)
SELECT ROUND(AVG(revenue), 2) AS average_order_value FROM fact_sales;

-- 6. Monthly revenue
SELECT d.year, d.month, SUM(f.revenue) AS monthly_revenue
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 7. Monthly transaction count
SELECT d.year, d.month, COUNT(*) AS monthly_transactions
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 8. Top products by revenue
SELECT p.product_id, p.product_name, SUM(f.revenue) AS total_revenue
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_id, p.product_name
ORDER BY total_revenue DESC
LIMIT 10;

-- 9. Revenue by product category
SELECT p.category, SUM(f.revenue) AS total_revenue
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- 10. Revenue by city
SELECT c.city, SUM(f.revenue) AS total_revenue
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.city
ORDER BY total_revenue DESC;

-- 11. Top customers by spending (grouped by the key, not the name)
SELECT c.customer_id, c.customer_name, SUM(f.revenue) AS total_spent
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY total_spent DESC
LIMIT 10;

-- 12. Customer purchase frequency
SELECT c.customer_id, c.customer_name, COUNT(*) AS total_purchases
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_id, c.customer_name
ORDER BY total_purchases DESC
LIMIT 10;

-- 13. Average revenue per customer (total revenue / number of distinct customers)
SELECT ROUND(SUM(revenue) * 1.0 / COUNT(DISTINCT customer_id), 2) AS avg_revenue_per_customer
FROM fact_sales;

-- 14. Profit by category
SELECT p.category, SUM(f.profit) AS total_profit
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY total_profit DESC;

-- 15. Best month by profit
SELECT d.year, d.month, SUM(f.profit) AS monthly_profit
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY monthly_profit DESC
LIMIT 1;

-- 16. Running total of revenue by month (window function)
WITH monthly AS (
    SELECT d.year, d.month, SUM(f.revenue) AS revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY d.year, d.month
)
SELECT year, month, revenue,
       SUM(revenue) OVER (ORDER BY year, month) AS running_revenue
FROM monthly
ORDER BY year, month;

-- 17. Month over month revenue growth (LAG)
WITH monthly AS (
    SELECT d.year, d.month, SUM(f.revenue) AS revenue
    FROM fact_sales f
    JOIN dim_date d ON f.date_id = d.date_id
    GROUP BY d.year, d.month
)
SELECT year, month, revenue,
       LAG(revenue) OVER (ORDER BY year, month) AS previous_month,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year, month))
             / LAG(revenue) OVER (ORDER BY year, month), 2) AS growth_pct
FROM monthly
ORDER BY year, month;

-- 18. Top 3 customers in each city (RANK)
WITH spend AS (
    SELECT c.city, c.customer_id, SUM(f.revenue) AS total_spent
    FROM fact_sales f
    JOIN dim_customer c ON f.customer_id = c.customer_id
    GROUP BY c.city, c.customer_id
),
ranked AS (
    SELECT city, customer_id, total_spent,
           RANK() OVER (PARTITION BY city ORDER BY total_spent DESC) AS city_rank
    FROM spend
)
SELECT city, customer_id, total_spent, city_rank
FROM ranked
WHERE city_rank <= 3
ORDER BY city, city_rank;
