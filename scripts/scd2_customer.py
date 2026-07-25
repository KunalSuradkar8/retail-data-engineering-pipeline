import os
import sys
import hashlib
import logging
from datetime import datetime
import pandas as pd
from typing import Tuple

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.database import PostgresConnectionManager
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger

class CustomerSCD2Processor:
    """
    Handles Slowly Changing Dimension Type 2 (SCD2) for Customer entity.
    Tracks history using effective_start_date, effective_end_date, and is_current flag.
    """
    def __init__(self, config_loader: ConfigLoader, logger: logging.Logger = None):
        self.config = config_loader
        self.logger = logger or setup_logger("scd2_customer")
        self.db_config = self.config.db_credentials
        self.schema = self.config.get("database.target_schema", "retail")

    @staticmethod
    def calculate_hash(row: pd.Series) -> str:
        """Calculates MD5 hash diff across customer attributes for change tracking."""
        name = str(row.get('name', ''))
        email = str(row.get('email', ''))
        address = str(row.get('address', ''))
        city = str(row.get('city', ''))
        concat_str = f"{name}|{email}|{address}|{city}"
        return hashlib.md5(concat_str.encode('utf-8')).hexdigest()

    def process_customer_scd2(self, incoming_df: pd.DataFrame) -> Tuple[int, int]:
        """
        Executes SCD Type 2 algorithm on incoming customer DataFrame.
        Returns (new_inserts_count, updated_expirations_count).
        """
        if incoming_df.empty or "customer_id" not in incoming_df.columns:
            self.logger.warning("Incoming Customer DataFrame is empty or missing 'customer_id'. Skipping SCD2.")
            return 0, 0

        incoming_df = incoming_df.copy()
        incoming_df['hash_diff'] = incoming_df.apply(self.calculate_hash, axis=1)

        with PostgresConnectionManager(self.db_config, logger=self.logger) as db:
            db.initialize_dim_tables()

            fetch_query = f"""
            SELECT customer_id, hash_diff 
            FROM {self.schema}.dim_customer 
            WHERE is_current = TRUE;
            """
            try:
                db.cursor.execute(fetch_query)
                active_records = {row[0]: row[1] for row in db.cursor.fetchall()}
            except Exception:
                active_records = {}

            records_to_expire = []
            records_to_insert = []
            now_ts = datetime.now()

            for _, row in incoming_df.iterrows():
                cust_id = int(row['customer_id'])
                new_hash = row['hash_diff']

                if cust_id not in active_records:
                    records_to_insert.append((
                        cust_id, row.get('name'), row.get('email'), 
                        row.get('address'), row.get('city'), new_hash, now_ts, None, True
                    ))
                elif active_records[cust_id] != new_hash:
                    records_to_expire.append((now_ts, cust_id))
                    records_to_insert.append((
                        cust_id, row.get('name'), row.get('email'), 
                        row.get('address'), row.get('city'), new_hash, now_ts, None, True
                    ))

            if records_to_expire:
                expire_query = f"""
                UPDATE {self.schema}.dim_customer
                SET is_current = FALSE, effective_end_date = %s
                WHERE customer_id = %s AND is_current = TRUE;
                """
                db.cursor.executemany(expire_query, records_to_expire)
                self.logger.info(f"Expired {len(records_to_expire)} historical customer records.")

            if records_to_insert:
                insert_query = f"""
                INSERT INTO {self.schema}.dim_customer (
                    customer_id, name, email, address, city, hash_diff, 
                    effective_start_date, effective_end_date, is_current
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                db.cursor.executemany(insert_query, records_to_insert)
                self.logger.info(f"Inserted {len(records_to_insert)} new/updated customer records.")

            return len(records_to_insert), len(records_to_expire)
