import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import glob
import pandas as pd
import logging
from typing import Optional, Tuple
from utils.logger import setup_logger
from utils.config_loader import ConfigLoader

class DataExtractor:
    """
    Extracts raw CSV files from raw directory.
    """
    def __init__(self, config_loader: ConfigLoader, logger: Optional[logging.Logger] = None):
        self.config = config_loader
        log_dir = self.config.get("log_config.log_dir", "logs")
        log_file = self.config.get("log_config.log_file", "pipeline.log")
        log_level = self.config.get("log_config.log_level", "INFO")
        
        self.logger = logger or setup_logger("extractor", log_dir=log_dir, log_file=log_file, log_level=log_level)
        
        raw_path = self.config.get("data_paths.raw_dir", "data/raw")
        if not os.path.isabs(raw_path):
            raw_path = os.path.join(PROJECT_ROOT, raw_path)
        self.raw_dir = raw_path

    def get_latest_csv_file(self) -> Optional[str]:
        """
        Scans raw directory and returns the oldest CSV file (FIFO order). Ignores hidden files.
        """
        search_pattern = os.path.join(self.raw_dir, "*.csv")
        csv_files = [f for f in glob.glob(search_pattern) if not os.path.basename(f).startswith('.')]
        
        if not csv_files:
            self.logger.info(f"No CSV files found in raw directory: {self.raw_dir}")
            return None
            
        csv_files.sort(key=os.path.getmtime)
        selected_file = csv_files[0]
        self.logger.info(f"Selected file for extraction: {selected_file}")
        return selected_file

    def extract(self) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Extracts data from selected CSV file into a Pandas DataFrame.
        """
        file_path = self.get_latest_csv_file()
        if not file_path:
            return None, None
            
        try:
            self.logger.info(f"Extracting data from {file_path}...")
            df = pd.read_csv(file_path)
            self.logger.info(f"Successfully extracted {len(df)} rows from {file_path}.")
            return df, file_path
        except pd.errors.EmptyDataError:
            self.logger.warning(f"File {file_path} is empty.")
            return pd.DataFrame(), file_path
        except Exception as e:
            self.logger.error(f"Error occurred while extracting {file_path}: {e}")
            raise e
