import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import shutil
import logging
from datetime import datetime
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger
from scripts.extract import DataExtractor
from scripts.validation import DataValidator
from scripts.transform import DataTransformer
from scripts.load import DataLoader

def archive_processed_file(file_path: str, archive_dir: str, logger: logging.Logger) -> None:
    """
    Moves processed raw file to the archive directory with a timestamp.
    """
    try:
        os.makedirs(archive_dir, exist_ok=True)
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_filename = f"{timestamp}_{filename}"
        destination_path = os.path.join(archive_dir, archived_filename)
        
        shutil.move(file_path, destination_path)
        logger.info(f"Successfully archived raw file '{file_path}' to '{destination_path}'.")
    except Exception as e:
        logger.error(f"Failed to archive file '{file_path}': {e}")
        raise e

def run_pipeline() -> None:
    """
    Main orchestration function for the Retail Data Engineering ETL Pipeline.
    """
    config = ConfigLoader()
    log_dir = config.get("log_config.log_dir", "logs")
    log_file = config.get("log_config.log_file", "pipeline.log")
    log_level = config.get("log_config.log_level", "INFO")
    
    logger = setup_logger("main_orchestrator", log_dir=log_dir, log_file=log_file, log_level=log_level)
    logger.info("==================================================")
    logger.info("Starting Retail Data Engineering ETL Pipeline Job")
    logger.info("==================================================")

    archive_dir = config.get("data_paths.archive_dir", "data/archive")
    if not os.path.isabs(archive_dir):
        archive_dir = os.path.join(PROJECT_ROOT, archive_dir)

    try:
        # Step 1: Extraction
        logger.info("--- Step 1: Data Extraction ---")
        extractor = DataExtractor(config, logger=logger)
        raw_df, file_path = extractor.extract()

        if file_path is None:
            logger.info("Pipeline Execution Ended: No files present in raw directory to process.")
            return

        # Step 2: Validation
        logger.info("--- Step 2: Data Validation ---")
        validator = DataValidator(config, logger=logger)
        good_df, bad_df = validator.validate(raw_df)

        if good_df.empty:
            logger.warning("No valid records remaining after validation phase. Skipping transformation and load.")
            archive_processed_file(file_path, archive_dir, logger)
            logger.info("Pipeline completed with 0 records loaded.")
            return

        # Step 3: Transformation
        logger.info("--- Step 3: Data Transformation ---")
        transformer = DataTransformer(config, logger=logger)
        transformed_df = transformer.transform(good_df)

        # Step 4: Loading
        logger.info("--- Step 4: Database Loading ---")
        loader = DataLoader(config, logger=logger)
        rows_inserted = loader.load(transformed_df)

        # Step 5: Archiving
        logger.info("--- Step 5: Archiving Processed Data ---")
        archive_processed_file(file_path, archive_dir, logger)

        logger.info("==================================================")
        logger.info(f"ETL Pipeline Job Completed Successfully! Total Rows Loaded: {rows_inserted}")
        logger.info("==================================================")

    except Exception as e:
        logger.critical(f"ETL Pipeline Failed unexpectedly with Error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_pipeline()
