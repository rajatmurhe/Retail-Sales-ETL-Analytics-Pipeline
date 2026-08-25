-- USE THE RIGHT DATABASE
USE retail_db;

-- 1. Total Revenue
SELECT SUM(revenue) AS total_revenue FROM fact_sales;

-- 2. Total Transactions (Proving we have 10,000+)
SELECT COUNT(transaction_id) AS total_transactions FROM fact_sales;

-- 3. Total Units Sold
SELECT SUM(quantity) AS total_units_sold FROM fact_sales;

-- 4. Total Profit
SELECT SUM(profit) AS total_profit FROM fact_sales;

-- 5. Average Order Value (AOV)
SELECT AVG(revenue) AS average_order_value FROM fact_sales;

-- 6. Monthly Revenue
SELECT d.year, d.month, SUM(f.revenue) AS monthly_revenue 
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 7. Monthly Transaction Trends
SELECT d.year, d.month, COUNT(f.transaction_id) AS total_monthly_transactions
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;

-- 8. Top Products by Revenue
SELECT p.product_name, SUM(f.revenue) AS total_revenue
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.product_name
ORDER BY total_revenue DESC
LIMIT 10;

-- 9. Revenue by Product Category
SELECT p.category, SUM(f.revenue) AS total_revenue
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC;

-- 10. Revenue by Region/City
SELECT c.city, SUM(f.revenue) AS total_revenue
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.city
ORDER BY total_revenue DESC;

-- 11. Top Customers by Spending
SELECT c.customer_name, SUM(f.revenue) AS total_spent
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_name
ORDER BY total_spent DESC
LIMIT 10;

-- 12. Customer Purchase Frequency (Who buys the most often?)
SELECT c.customer_name, COUNT(f.transaction_id) AS total_purchases
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_name
ORDER BY total_purchases DESC
LIMIT 10;

-- 13. Average Revenue Per Customer
SELECT c.customer_name, AVG(f.revenue) AS avg_spent_per_transaction
FROM fact_sales f
JOIN dim_customer c ON f.customer_id = c.customer_id
GROUP BY c.customer_name
ORDER BY avg_spent_per_transaction DESC
LIMIT 10;

-- 14. Profit by Category
SELECT p.category, SUM(f.profit) AS total_profit
FROM fact_sales f
JOIN dim_product p ON f.product_id = p.product_id
GROUP BY p.category
ORDER BY total_profit DESC;

-- 15. Best-Performing Month by Profit
SELECT d.year, d.month, SUM(f.profit) AS max_profit
FROM fact_sales f
JOIN dim_date d ON f.date_id = d.date_id
GROUP BY d.year, d.month
ORDER BY max_profit DESC
LIMIT 1;