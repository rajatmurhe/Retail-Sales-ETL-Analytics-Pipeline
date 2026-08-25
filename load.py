import pandas as pd
from sqlalchemy import create_engine

print("Starting Load Phase...")

# 1. Connect to MySQL (Change 'your_password' to your actual password)
# Format: mysql+pymysql://username:password@localhost/database_name
engine = create_engine("mysql+pymysql://root:708970@localhost/retail_db")

# 2. Read the clean CSVs we just made
print("Reading clean data...")
dim_customer = pd.read_csv('data/processed/dim_customer.csv')
dim_product = pd.read_csv('data/processed/dim_product.csv')
dim_date = pd.read_csv('data/processed/dim_date.csv')
fact_sales = pd.read_csv('data/processed/fact_sales.csv')

# 3. Load them into MySQL
print("Loading into MySQL Data Warehouse...")
dim_customer.to_sql('dim_customer', con=engine, if_exists='replace', index=False)
dim_product.to_sql('dim_product', con=engine, if_exists='replace', index=False)
dim_date.to_sql('dim_date', con=engine, if_exists='replace', index=False)
fact_sales.to_sql('fact_sales', con=engine, if_exists='replace', index=False)

print("SUCCESS! All 4 tables are now in MySQL.")