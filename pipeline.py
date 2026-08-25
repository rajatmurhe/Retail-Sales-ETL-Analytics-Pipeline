import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

print("Starting ETL Pipeline...")

# Create folders to save our data
os.makedirs('data/processed', exist_ok=True)

# ==========================================
# 1. EXTRACT: GENERATE RAW DATA
# ==========================================
print("Generating 12,000 transactions...")
np.random.seed(42)

# Fake Products
products = {
    'P01': ('Laptop', 'Electronics', 800, 600),
    'P02': ('Mouse', 'Electronics', 25, 10),
    'P03': ('Desk', 'Furniture', 150, 80),
    'P04': ('Chair', 'Furniture', 100, 50),
    'P05': ('Pen', 'Office Supplies', 5, 1)
}

# Fake Customers
customers = [{'customer_id': f'C{i:04d}', 'customer_name': f'Customer_{i}', 'city': random.choice(['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Pune'])} for i in range(1, 501)]

# Generate 12000 Transactions
transactions = []
start_date = datetime(2023, 1, 1)

for i in range(1, 12001):
    prod_id = random.choice(list(products.keys()))
    cust = random.choice(customers)
    qty = random.randint(1, 5)
    days_to_add = random.randint(0, 365)
    txn_date = start_date + timedelta(days=days_to_add)
    
    transactions.append({
        'transaction_id': f'T{i:05d}',
        'date': txn_date.strftime('%Y-%m-%d'),
        'customer_id': cust['customer_id'],
        'customer_name': cust['customer_name'],
        'city': cust['city'],
        'product_id': prod_id,
        'product_name': products[prod_id][0],
        'category': products[prod_id][1],
        'price': products[prod_id][2],
        'cost': products[prod_id][3],
        'quantity': qty
    })

# Load into Pandas DataFrame
df_raw = pd.DataFrame(transactions)

# ==========================================
# 2. TRANSFORM: CLEAN & CALCULATE
# ==========================================
print("Transforming data and calculating metrics...")

# Calculate Revenue and Profit
df_raw['revenue'] = df_raw['price'] * df_raw['quantity']
df_raw['total_cost'] = df_raw['cost'] * df_raw['quantity']
df_raw['profit'] = df_raw['revenue'] - df_raw['total_cost']

# Drop any accidental duplicates or missing values (Data Cleaning)
df_raw = df_raw.drop_duplicates()
df_raw = df_raw.dropna()

# ==========================================
# 3. STAR SCHEMA: SPLIT INTO 4 TABLES
# ==========================================
print("Building Star Schema...")

# Table 1: dim_customer (Drop duplicates so each customer appears only once)
dim_customer = df_raw[['customer_id', 'customer_name', 'city']].drop_duplicates().reset_index(drop=True)

# Table 2: dim_product
dim_product = df_raw[['product_id', 'product_name', 'category', 'price', 'cost']].drop_duplicates().reset_index(drop=True)

# Table 3: dim_date
df_raw['date'] = pd.to_datetime(df_raw['date'])
dim_date = pd.DataFrame({'date': df_raw['date'].unique()})
dim_date['date_id'] = dim_date['date'].dt.strftime('%Y%m%d').astype(int)
dim_date['year'] = dim_date['date'].dt.year
dim_date['month'] = dim_date['date'].dt.month
dim_date['day'] = dim_date['date'].dt.day

# Table 4: fact_sales (The main register linking everything)
# We create date_id in raw data to link it
df_raw['date_id'] = df_raw['date'].dt.strftime('%Y%m%d').astype(int)
fact_sales = df_raw[['transaction_id', 'date_id', 'customer_id', 'product_id', 'quantity', 'revenue', 'profit']]

# ==========================================
# 4. LOAD: SAVE TO CSV FOR MYSQL
# ==========================================
print("Saving tables...")
fact_sales.to_csv('data/processed/fact_sales.csv', index=False)
dim_customer.to_csv('data/processed/dim_customer.csv', index=False)
dim_product.to_csv('data/processed/dim_product.csv', index=False)
dim_date.to_csv('data/processed/dim_date.csv', index=False)

print(f"SUCCESS! Created fact_sales with {len(fact_sales)} rows.")