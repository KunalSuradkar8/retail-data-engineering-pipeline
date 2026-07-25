import os
import json
import sqlite3
import pandas as pd

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
raw_dir = os.path.join(PROJECT_ROOT, "data", "raw")

# 1. Folders
csv_dir = os.path.join(raw_dir, "csv_source")
api_dir = os.path.join(raw_dir, "api_source")
sql_dir = os.path.join(raw_dir, "sqlite_source")
json_dir = os.path.join(raw_dir, "json_source")

os.makedirs(csv_dir, exist_ok=True)
os.makedirs(api_dir, exist_ok=True)
os.makedirs(sql_dir, exist_ok=True)
os.makedirs(json_dir, exist_ok=True)

# 1. CSV Orders
csv_data = [
    {"order_id": 1001, "customer_id": 201, "product_id": 501, "quantity": 2, "price": 150.00},
    {"order_id": 1002, "customer_id": 202, "product_id": 502, "quantity": 1, "price": 899.99},
    {"order_id": 1003, "customer_id": 203, "product_id": 503, "quantity": 4, "price": 45.50},
]
pd.DataFrame(csv_data).to_csv(os.path.join(csv_dir, "store_orders.csv"), index=False)

# 2. API Payments JSON
api_data = [
    {"transaction_id": "TXN_9001", "order_id": 1001, "payment_mode": "UPI", "status": "SUCCESS"},
    {"transaction_id": "TXN_9002", "order_id": 1002, "payment_mode": "CREDIT_CARD", "status": "SUCCESS"},
    {"transaction_id": "TXN_9003", "order_id": 1003, "payment_mode": "NET_BANKING", "status": "PENDING"}
]
with open(os.path.join(api_dir, "payments_api.json"), "w") as f:
    json.dump(api_data, f, indent=2)

# 3. SQLite Relational Database
db_path = os.path.join(sql_dir, "oltp_retail.db")
conn = sqlite3.connect(db_path)
cust_df = pd.DataFrame([
    {"customer_id": 201, "name": "Rahul Sharma", "email": "rahul@example.com", "city": "Mumbai"},
    {"customer_id": 202, "name": "Priya Patel", "email": "priya@example.com", "city": "Pune"},
    {"customer_id": 203, "name": "Amit Kumar", "email": "amit@example.com", "city": "Delhi"},
])
cust_df.to_sql("customers", conn, if_exists="replace", index=False)
conn.close()

# 4. Clickstream JSON
json_data = [
    {"session_id": "SESS_101", "customer_id": 201, "event": "ADD_TO_CART", "device": "Mobile"},
    {"session_id": "SESS_102", "customer_id": 202, "event": "CHECKOUT", "device": "Desktop"},
    {"session_id": "SESS_103", "customer_id": 203, "event": "SEARCH", "device": "Tablet"}
]
with open(os.path.join(json_dir, "web_clickstream.json"), "w") as f:
    json.dump(json_data, f, indent=2)

print("[Success] Multi-Source Folders and Data Files successfully generated!")
