import os
import sys
import logging
import pandas as pd
from typing import Dict
from utils.database import PostgresConnectionManager
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger

class CDCProcessor:
    """
    Change Data Capture (CDC) engine to identify INSERT, UPDATE operations
    and persist audit log lineage in PostgreSQL.
    """
    def __init__(self, config_loader: ConfigLoader, logger: logging.Logger = None):
        self.config = config_loader
        self.logger = logger or setup_logger("cdc_processor")
        self.db_config = self.config.db_credentials
        self.schema = self.config.get("database.target_schema", "retail")

    def capture_changes(self, table_name: str, incoming_df: pd.DataFrame, key_column: str) -> Dict[str, int]:
        """
        Detects CDC delta operations for incoming batch dataframe compared to target table state.
        """
        if incoming_df.empty or key_column not in incoming_df.columns:
            return {"INSERT": 0, "UPDATE": 0}

        summary = {"INSERT": 0, "UPDATE": 0}
        audit_entries = []

        with PostgresConnectionManager(self.db_config, logger=self.logger) as db:
            db.initialize_dim_tables()

            fetch_query = f"SELECT {key_column} FROM {self.schema}.{table_name};"
            try:
                db.cursor.execute(fetch_query)
                existing_ids = {row[0] for row in db.cursor.fetchall()}
            except Exception:
                existing_ids = set()

            for _, row in incoming_df.iterrows():
                rec_id = int(row[key_column])
                action = "INSERT" if rec_id not in existing_ids else "UPDATE"
                summary[action] += 1
                audit_entries.append((table_name, rec_id, action, f"CDC captured {action} for key {rec_id}"))

            if audit_entries:
                log_query = f"""
                INSERT INTO {self.schema}.cdc_audit_log (table_name, record_id, action_type, details)
                VALUES (%s, %s, %s, %s);
                """
                db.cursor.executemany(log_query, audit_entries)
                self.logger.info(f"CDC Summary for table '{table_name}': {summary}")

        return summary
