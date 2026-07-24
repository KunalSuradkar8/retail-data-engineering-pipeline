import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import logging
from datetime import datetime, timezone
from typing import Optional
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader

class DataTransformer:
    """
    Applies data transformations, explicit type casting, derived columns, and audit timestamps.
    """
    def __init__(self, config_loader: ConfigLoader, logger: Optional[logging.Logger] = None):
        self.config = config_loader
        log_dir = self.config.get("log_config.log_dir", "logs")
        log_file = self.config.get("log_config.log_file", "pipeline.log")
        log_level = self.config.get("log_config.log_level", "INFO")
        
        self.logger = logger or setup_logger("transformer", log_dir=log_dir, log_file=log_file, log_level=log_level)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies 4 Transformation steps on Validated DataFrame.
        """
        if df is None or df.empty:
            self.logger.warning("Transformation skipped: Received empty or None DataFrame.")
            return pd.DataFrame()

        self.logger.info(f"Starting data transformation on {len(df)} records...")
        transformed_df = df.copy()

        # Step 1: Deduplication safeguard
        initial_len = len(transformed_df)
        transformed_df.drop_duplicates(subset=["order_id"], keep="first", inplace=True)
        if len(transformed_df) < initial_len:
            self.logger.info(f"Removed {initial_len - len(transformed_df)} duplicate order_id records during transformation.")

        # Step 2: Convert datatypes explicitly
        try:
            transformed_df["order_id"] = transformed_df["order_id"].astype(int)
            transformed_df["customer_id"] = transformed_df["customer_id"].astype(int)
            transformed_df["product_id"] = transformed_df["product_id"].astype(int)
            transformed_df["quantity"] = transformed_df["quantity"].astype(int)
            transformed_df["price"] = transformed_df["price"].astype(float)
            self.logger.info("Successfully converted column datatypes.")
        except Exception as e:
            self.logger.error(f"Datatype conversion failed: {e}")
            raise e

        # Step 3: Calculate total_amount derived column
        transformed_df["total_amount"] = (transformed_df["quantity"] * transformed_df["price"]).round(2)
        self.logger.info("Successfully calculated 'total_amount' derived column.")

        # Step 4: Add load_timestamp audit column (UTC)
        current_utc_time = datetime.now(timezone.utc)
        transformed_df["load_timestamp"] = current_utc_time
        self.logger.info("Successfully added 'load_timestamp' audit column.")

        self.logger.info(f"Transformation complete. Prepared {len(transformed_df)} rows for load step.")
        return transformed_df
