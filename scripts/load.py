import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import logging
from typing import Optional
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader
from utils.database import PostgresConnectionManager

class DataLoader:
    """
    Handles idempotent bulk loading of transformed DataFrames into PostgreSQL target table using UPSERT.
    """
    def __init__(self, config_loader: ConfigLoader, logger: Optional[logging.Logger] = None):
        self.config = config_loader
        log_dir = self.config.get("log_config.log_dir", "logs")
        log_file = self.config.get("log_config.log_file", "pipeline.log")
        log_level = self.config.get("log_config.log_level", "INFO")
        
        self.logger = logger or setup_logger("loader", log_dir=log_dir, log_file=log_file, log_level=log_level)
        self.target_schema = self.config.get("database.target_schema", "retail")
        self.target_table = self.config.get("database.target_table", "orders")
        self.db_config = self.config.db_credentials

    def load(self, df: pd.DataFrame) -> int:
        """
        Bulk inserts/updates transformed DataFrame into PostgreSQL using execute_values.
        """
        if df is None or df.empty:
            self.logger.warning("Load step skipped: Input DataFrame is empty or None.")
            return 0

        self.logger.info(f"Preparing to load {len(df)} records into {self.target_schema}.{self.target_table}...")

        columns = ["order_id", "customer_id", "product_id", "quantity", "price", "total_amount", "load_timestamp"]
        
        data_tuples = [tuple(x) for x in df[columns].to_numpy()]

        insert_query = f"""
        INSERT INTO {self.target_schema}.{self.target_table} (
            order_id, customer_id, product_id, quantity, price, total_amount, load_timestamp
        ) VALUES %s
        ON CONFLICT (order_id) DO UPDATE SET
            customer_id = EXCLUDED.customer_id,
            product_id = EXCLUDED.product_id,
            quantity = EXCLUDED.quantity,
            price = EXCLUDED.price,
            total_amount = EXCLUDED.total_amount,
            load_timestamp = EXCLUDED.load_timestamp;
        """

        try:
            with PostgresConnectionManager(self.db_config, logger=self.logger) as db:
                db.initialize_db()
                rows_inserted = db.insert_bulk(insert_query, data_tuples)
                self.logger.info(f"Successfully loaded {rows_inserted} records into database table '{self.target_schema}.{self.target_table}'.")
                return rows_inserted
        except Exception as e:
            self.logger.error(f"Failed to load data into database: {e}")
            raise e
