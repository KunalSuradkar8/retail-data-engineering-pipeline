import os
import sys
import glob
import json
import sqlite3
import logging
import pandas as pd
from typing import Dict, Optional

try:
    import psycopg2
    HAS_POSTGRES = True
except ImportError:
    HAS_POSTGRES = False

try:
    import pymysql
    HAS_MYSQL = True
except ImportError:
    HAS_MYSQL = False

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger

class MultiSourceExtractor:
    """
    Enterprise Multi-Source Data Extractor for:
    1. CSV Files (Local Store Orders)
    2. REST API JSON (Payment Gateway Invoices)
    3. SQLite Database (Local OLTP DB)
    4. PostgreSQL Database (Enterprise ERP DB)
    5. MySQL Database (E-Commerce Web/Cart DB)
    6. JSON Documents (Web Clickstream Sessions)
    """
    def __init__(self, config_loader: ConfigLoader, logger: Optional[logging.Logger] = None):
        self.config = config_loader
        self.logger = logger or setup_logger("multi_source_extractor")
        
        raw_path = self.config.get("data_paths.raw_dir", "data/raw")
        if not os.path.isabs(raw_path):
            raw_path = os.path.join(PROJECT_ROOT, raw_path)
        self.raw_dir = raw_path

    def extract_from_csv(self) -> pd.DataFrame:
        """1. Extract data from CSV Files (Store Orders)."""
        csv_dir = os.path.join(self.raw_dir, "csv_source")
        csv_files = glob.glob(os.path.join(csv_dir, "*.csv"))
        if not csv_files:
            self.logger.warning(f"[CSV Source] No CSV files found in {csv_dir}")
            return pd.DataFrame()
        
        file_path = csv_files[0]
        try:
            self.logger.info(f"[CSV Source] Extracting data from {file_path}...")
            return pd.read_csv(file_path)
        except pd.errors.EmptyDataError:
            self.logger.warning(f"[CSV Source] File {file_path} is empty.")
            return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"[CSV Source] Failed to read {file_path}: {e}")
            return pd.DataFrame()

    def extract_from_api_json(self) -> pd.DataFrame:
        """2. Extract data from REST API JSON payloads (Payment Gateways)."""
        api_dir = os.path.join(self.raw_dir, "api_source")
        json_files = glob.glob(os.path.join(api_dir, "*.json"))
        if not json_files:
            self.logger.warning(f"[API Source] No JSON API files found in {api_dir}")
            return pd.DataFrame()

        file_path = json_files[0]
        try:
            self.logger.info(f"[API Source] Extracting JSON payload from {file_path}...")
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception as e:
            self.logger.error(f"[API Source] Failed to read JSON payload {file_path}: {e}")
            return pd.DataFrame()

    def extract_from_sqlite(self) -> pd.DataFrame:
        """3. Extract data from SQLite Relational Database."""
        db_path = os.path.join(self.raw_dir, "sqlite_source", "oltp_retail.db")
        if not os.path.exists(db_path):
            db_path = os.path.join(self.raw_dir, "sqllite_source", "oltp_retail.db")

        if not os.path.exists(db_path):
            self.logger.warning(f"[SQLite Source] Database not found at {db_path}")
            return pd.DataFrame()

        self.logger.info(f"[SQLite Source] Querying SQLite database at {db_path}...")
        conn = sqlite3.connect(db_path)
        try:
            df = pd.read_sql_query("SELECT * FROM customers", conn)
            return df
        except Exception as e:
            self.logger.warning(f"[SQLite Source] Query failed: {e}")
            return pd.DataFrame()
        finally:
            conn.close()

    def extract_from_postgresql(self, query: str = "SELECT * FROM retail.orders") -> pd.DataFrame:
        """4. Extract data from PostgreSQL Database (Enterprise ERP DB)."""
        if not HAS_POSTGRES:
            self.logger.warning("[PostgreSQL Source] psycopg2 package not installed.")
            return pd.DataFrame()

        db_config = self.config.db_credentials
        try:
            self.logger.info(f"[PostgreSQL Source] Connecting to Host={db_config.get('host')}, DB={db_config.get('database')}...")
            conn = psycopg2.connect(
                host=db_config["host"],
                port=db_config.get("port", 5432),
                database=db_config["database"],
                user=db_config["user"],
                password=db_config["password"]
            )
            df = pd.read_sql_query(query, conn)
            conn.close()
            self.logger.info(f"[PostgreSQL Source] Extracted {len(df)} records.")
            return df
        except Exception as e:
            self.logger.warning(f"[PostgreSQL Source] Connection/query skipped: {e}")
            return pd.DataFrame()

    def extract_from_mysql(self, query: str = "SELECT * FROM ecommerce.orders") -> pd.DataFrame:
        """5. Extract data from MySQL Database (E-Commerce Web Cart DB)."""
        if not HAS_MYSQL:
            self.logger.warning("[MySQL Source] PyMySQL package not installed.")
            return pd.DataFrame()

        mysql_config = self.config.get("multi_source.mysql", {})
        if not mysql_config or "host" not in mysql_config:
            self.logger.warning("[MySQL Source] No MySQL configuration found in config.json.")
            return pd.DataFrame()

        try:
            self.logger.info(f"[MySQL Source] Connecting to Host={mysql_config.get('host')}, DB={mysql_config.get('database')}...")
            conn = pymysql.connect(
                host=mysql_config["host"],
                port=mysql_config.get("port", 3306),
                database=mysql_config["database"],
                user=mysql_config["user"],
                password=mysql_config["password"]
            )
            df = pd.read_sql_query(query, conn)
            conn.close()
            self.logger.info(f"[MySQL Source] Extracted {len(df)} records.")
            return df
        except Exception as e:
            self.logger.warning(f"[MySQL Source] Connection/query skipped: {e}")
            return pd.DataFrame()

    def extract_from_clickstream_json(self) -> pd.DataFrame:
        """6. Extract data from Web Clickstream JSON documents."""
        json_dir = os.path.join(self.raw_dir, "json_source")
        files = glob.glob(os.path.join(json_dir, "*.json"))
        if not files:
            self.logger.warning(f"[Clickstream JSON Source] No JSON files found in {json_dir}")
            return pd.DataFrame()

        file_path = files[0]
        try:
            self.logger.info(f"[Clickstream JSON Source] Extracting clickstream from {file_path}...")
            return pd.read_json(file_path)
        except Exception as e:
            self.logger.error(f"[Clickstream JSON Source] Failed to read {file_path}: {e}")
            return pd.DataFrame()

    def extract_all_sources(self) -> Dict[str, pd.DataFrame]:
        """Extract data from all enterprise sources simultaneously."""
        self.logger.info("==================================================")
        self.logger.info("Starting Multi-Source Enterprise Extraction Engine")
        self.logger.info("==================================================")
        
        extracted_data = {
            "csv_orders": self.extract_from_csv(),
            "api_payments": self.extract_from_api_json(),
            "sqlite_customers": self.extract_from_sqlite(),
            "postgresql_orders": self.extract_from_postgresql(),
            "mysql_cart": self.extract_from_mysql(),
            "clickstream_events": self.extract_from_clickstream_json()
        }

        print("\n=== Multi-Source Extraction Summary ===")
        for source_name, df in extracted_data.items():
            record_count = len(df) if not df.empty else 0
            print(f"- Source '{source_name}': {record_count} records extracted.")
            self.logger.info(f"Source '{source_name}': {record_count} records extracted.")

        return extracted_data

if __name__ == "__main__":
    config = ConfigLoader()
    extractor = MultiSourceExtractor(config)
    results = extractor.extract_all_sources()
