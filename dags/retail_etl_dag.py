import os
import sys
from datetime import datetime, timedelta

# Try importing Airflow; fallback gracefully if Airflow package is not installed locally
try:
    from airflow import DAG  # type: ignore
    from airflow.operators.python import PythonOperator  # type: ignore
    HAS_AIRFLOW = True
except ImportError:
    HAS_AIRFLOW = False

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger
from scripts.multi_source_extractor import MultiSourceExtractor
from scripts.validation import DataValidator
from scripts.transform import DataTransformer
from scripts.cdc_handler import CDCProcessor
from scripts.scd2_customer import CustomerSCD2Processor
from scripts.load import DataLoader
from scripts.main import archive_processed_file

def execute_full_etl():
    """Multi-Source Retail ETL Pipeline Execution."""
    config = ConfigLoader()
    logger = setup_logger("airflow_orchestrator")
    
    print("\n=== Starting Multi-Source Retail ETL Pipeline Task ===")
    logger.info("Starting Multi-Source Retail ETL Pipeline Execution...")
    
    # Step 1: Multi-Source Extraction
    multi_extractor = MultiSourceExtractor(config, logger=logger)
    sources_data = multi_extractor.extract_all_sources()
    
    orders_df = sources_data.get("csv_orders")
    if orders_df is None or orders_df.empty:
        print("[Warning] No order records extracted from CSV source.")
        return

    print(f"[Step 1] Multi-Source Extraction Complete. Extracted {len(orders_df)} raw order records.")

    # Step 2: Validation
    validator = DataValidator(config, logger=logger)
    good_df, bad_df = validator.validate(orders_df)
    print(f"[Step 2] Validation Done: Good={len(good_df)}, Bad={len(bad_df)}")

    if good_df.empty:
        print("[Warning] No valid records remaining after validation.")
        return

    # Step 3: Transformation
    transformer = DataTransformer(config, logger=logger)
    transformed_df = transformer.transform(good_df)
    print(f"[Step 3] Transformed {len(transformed_df)} records.")

    # Step 4: CDC & SCD2 Processing
    cdc_processor = CDCProcessor(config, logger=logger)
    cdc_summary = cdc_processor.capture_changes("orders", transformed_df, key_column="order_id")
    print(f"[Step 4] CDC Summary: {cdc_summary}")

    customers_df = sources_data.get("sqlite_customers")
    if customers_df is not None and not customers_df.empty:
        scd2_processor = CustomerSCD2Processor(config, logger=logger)
        inserts, expires = scd2_processor.process_customer_scd2(customers_df)
        print(f"[Step 4.5] SCD2 Customer Dimension Updated: New Inserts={inserts}, Expired Old={expires}")

    # Step 5: Database Load
    loader = DataLoader(config, logger=logger)
    rows_inserted = loader.load(transformed_df)
    print(f"[Step 5] Database Load complete. Rows loaded into PostgreSQL: {rows_inserted}\n")

if HAS_AIRFLOW:
    default_args = {
        'owner': 'data_engineering_team',
        'start_date': datetime(2026, 1, 1),
        'retries': 1,
        'retry_delay': timedelta(minutes=2),
    }

    with DAG(
        'retail_etl_pipeline_dag',
        default_args=default_args,
        schedule_interval='0 0 * * *',
        catchup=False,
    ) as dag:
        run_etl_task = PythonOperator(
            task_id='execute_retail_etl_pipeline',
            python_callable=execute_full_etl,
        )

if __name__ == "__main__":
    execute_full_etl()
