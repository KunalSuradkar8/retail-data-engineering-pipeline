import os
import json
import sqlite3
import random
from datetime import datetime
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

# Generate dynamic IDs every time script is executed
base_order_id = random.randint(2000, 9000)
base_customer_id = random.randint(300, 800)

cities = ["Mumbai", "Pune", "Delhi", "Bangalore", "Hyderabad", "Chennai"]
names = ["Rahul Sharma", "Priya Patel", "Amit Kumar", "Sneha Rao", "Vikas Singh", "Ananya Das"]
devices = ["Mobile", "Desktop", "Tablet"]
events = ["SEARCH", "VIEW_ITEM", "ADD_TO_CART", "CHECKOUT"]
payment_modes = ["UPI", "CREDIT_CARD", "NET_BANKING", "DEBIT_CARD"]

csv_data = []
api_data = []
sql_cust_data = []
json_click_data = []

count = 10  # Generate 10 fresh dynamic records each run

for i in range(count):
    order_id = base_order_id + i
    cust_id = base_customer_id + (i % 5)
    prod_id = 500 + random.randint(1, 20)
    qty = random.randint(1, 5)
    price = round(random.uniform(20.0, 1500.0), 2)
    
    csv_data.append({
        "order_id": order_id,
        "customer_id": cust_id,
        "product_id": prod_id,
        "quantity": qty,
        "price": price
    })
    
    api_data.append({
        "transaction_id": f"TXN_{random.randint(10000, 99999)}",
        "order_id": order_id,
        "payment_mode": random.choice(payment_modes),
        "status": "SUCCESS" if random.random() > 0.1 else "FAILED"
    })
    
    if len(sql_cust_data) < 5:
        name = names[i % len(names)]
        email = f"{name.split()[0].lower()}{cust_id}@example.com"
        sql_cust_data.append({
            "customer_id": cust_id,
            "name": name,
            "email": email,
            "city": random.choice(cities)
        })
        
    json_click_data.append({
        "session_id": f"SESS_{random.randint(1000, 9999)}",
        "customer_id": cust_id,
        "event": random.choice(events),
        "device": random.choice(devices)
    })

# Write CSV Orders
pd.DataFrame(csv_data).to_csv(os.path.join(csv_dir, "store_orders.csv"), index=False)

# Write API Payments JSON
with open(os.path.join(api_dir, "payments_api.json"), "w") as f:
    json.dump(api_data, f, indent=2)

# Write SQLite Customers DB
db_path = os.path.join(sql_dir, "oltp_retail.db")
conn = sqlite3.connect(db_path)
pd.DataFrame(sql_cust_data).to_sql("customers", conn, if_exists="replace", index=False)
conn.close()

# Write Clickstream JSON
with open(os.path.join(json_dir, "web_clickstream.json"), "w") as f:
    json.dump(json_click_data, f, indent=2)

print(f"[Success] Generated {count} fresh dynamic records across all multi-source files!")
print(f"New Generated Order IDs: {base_order_id} to {base_order_id + count - 1}")
