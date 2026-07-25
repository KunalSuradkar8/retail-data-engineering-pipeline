import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import random
import pandas as pd
from datetime import datetime
from utils.config_loader import ConfigLoader

def generate_raw_retail_data(num_records: int = 1000):
    """
    Generates mock retail order records with 5% intentional bad data patterns for quality testing.
    """
    config = ConfigLoader()
    raw_dir = config.get("data_paths.raw_dir", "data/raw")
    if not os.path.isabs(raw_dir):
        raw_dir = os.path.join(PROJECT_ROOT, raw_dir)
        
    os.makedirs(raw_dir, exist_ok=True)
    
    print(f"\nGenerating {num_records} mock retail order records...")
    
    records = []
    base_order_id = random.randint(10000, 50000)
    
    for i in range(num_records):
        order_id = base_order_id + i
        customer_id = random.randint(1, 500)
        product_id = random.randint(501, 550)
        quantity = random.randint(1, 10)
        price = round(random.uniform(10.0, 500.0), 2)
        
        # Inject 5% bad data patterns for validation testing
        rand_val = random.random()
        if rand_val < 0.015:
            quantity = -1 * random.randint(1, 5)  # Invalid negative quantity
        elif rand_val < 0.03:
            price = -1 * round(random.uniform(10.0, 100.0), 2)  # Invalid negative price
        elif rand_val < 0.04:
            order_id = base_order_id + max(0, i - 2)  # Duplicate order_id
        elif rand_val < 0.05:
            customer_id = None  # Null customer_id
            
        records.append({
            "order_id": order_id,
            "customer_id": customer_id,
            "product_id": product_id,
            "quantity": quantity,
            "price": price
        })
        
    df = pd.DataFrame(records)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"orders_raw_{timestamp}.csv"
    file_path = os.path.join(raw_dir, file_name)
    
    df.to_csv(file_path, index=False)
    print(f"Generated {len(df)} records and saved to: {file_path}\n")
    return file_path

if __name__ == "__main__":
    generate_raw_retail_data(1000)
