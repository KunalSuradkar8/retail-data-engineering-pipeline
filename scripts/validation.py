import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
import logging
from typing import Tuple, Optional
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader

class DataValidator:
    """
    Validates DataFrames against defined business rules and data quality checks.
    Splits good records from bad records and persists invalid data with rejection reasons.
    """
    def __init__(self, config_loader: ConfigLoader, logger: Optional[logging.Logger] = None):
        self.config = config_loader
        log_dir = self.config.get("log_config.log_dir", "logs")
        log_file = self.config.get("log_config.log_file", "pipeline.log")
        log_level = self.config.get("log_config.log_level", "INFO")
        
        self.logger = logger or setup_logger("validator", log_dir=log_dir, log_file=log_file, log_level=log_level)
        
        bad_path = self.config.get("data_paths.bad_records_dir", "data/bad_records")
        if not os.path.isabs(bad_path):
            bad_path = os.path.join(PROJECT_ROOT, bad_path)
        self.bad_records_dir = bad_path
        
        self.required_columns = self.config.get("validation_rules.required_columns", [
            "order_id", "customer_id", "product_id", "quantity", "price"
        ])

    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Executes 6 Data Quality Checks on the input DataFrame.
        """
        # Rule 1: Empty file check
        if df is None or df.empty:
            self.logger.warning("Validation Failed: The input DataFrame is empty or None.")
            return pd.DataFrame(), pd.DataFrame()

        self.logger.info(f"Starting validation on {len(df)} records...")
        
        # Rule 2: Required columns check
        missing_cols = [col for col in self.required_columns if col not in df.columns]
        if missing_cols:
            self.logger.error(f"Validation Failed: Missing required columns: {missing_cols}")
            bad_df = df.copy()
            bad_df["rejection_reason"] = f"Missing required columns: {missing_cols}"
            self._save_bad_records(bad_df)
            return pd.DataFrame(), bad_df

        work_df = df.copy()
        work_df["rejection_reason"] = ""

        # Rule 3: Null Check
        null_mask = work_df[self.required_columns].isnull().any(axis=1)
        work_df.loc[null_mask, "rejection_reason"] += "Null values found; "

        # Rule 4: Duplicate Check (on order_id)
        duplicate_mask = work_df.duplicated(subset=["order_id"], keep=False)
        work_df.loc[duplicate_mask, "rejection_reason"] += "Duplicate order_id found; "

        # Rule 5: Negative / Zero Quantity Check
        quantity_numeric = pd.to_numeric(work_df["quantity"], errors="coerce")
        invalid_qty_mask = quantity_numeric.isna() | (quantity_numeric <= 0)
        work_df.loc[invalid_qty_mask, "rejection_reason"] += "Invalid/Negative quantity; "

        # Rule 6: Invalid Price Check (Price <= 0)
        price_numeric = pd.to_numeric(work_df["price"], errors="coerce")
        invalid_price_mask = price_numeric.isna() | (price_numeric <= 0)
        work_df.loc[invalid_price_mask, "rejection_reason"] += "Invalid/Negative price; "

        combined_bad_mask = null_mask | duplicate_mask | invalid_qty_mask | invalid_price_mask

        bad_df = work_df[combined_bad_mask].copy()
        good_df = work_df[~combined_bad_mask].copy()

        good_df.drop(columns=["rejection_reason"], inplace=True)

        self.logger.info(f"Validation summary: Total={len(df)}, Good={len(good_df)}, Bad={len(bad_df)}")

        if not bad_df.empty:
            self._save_bad_records(bad_df)

        return good_df, bad_df

    def _save_bad_records(self, bad_df: pd.DataFrame) -> None:
        """
        Saves invalid records to data/bad_records/bad_orders.csv
        """
        os.makedirs(self.bad_records_dir, exist_ok=True)
        target_path = os.path.join(self.bad_records_dir, "bad_orders.csv")
        
        if "rejection_reason" in bad_df.columns:
            bad_df["rejection_reason"] = bad_df["rejection_reason"].astype(str).str.rstrip("; ")

        file_exists = os.path.exists(target_path)
        bad_df.to_csv(target_path, mode="a" if file_exists else "w", index=False, header=not file_exists)
        self.logger.warning(f"Persisted {len(bad_df)} bad records to {target_path}")
