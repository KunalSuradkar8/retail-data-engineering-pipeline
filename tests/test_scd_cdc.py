import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from utils.config_loader import ConfigLoader
from scripts.scd2_customer import CustomerSCD2Processor
from scripts.cdc_handler import CDCProcessor

@pytest.fixture
def config():
    return ConfigLoader()

def test_scd2_hash_calculation(config):
    row1 = pd.Series({'name': 'John Doe', 'email': 'john@example.com', 'address': '123 Main St', 'city': 'NY'})
    row2 = pd.Series({'name': 'John Doe', 'email': 'john@example.com', 'address': '123 Main St', 'city': 'NY'})
    row3 = pd.Series({'name': 'John Doe', 'email': 'john_new@example.com', 'address': '123 Main St', 'city': 'NY'})
    
    hash1 = CustomerSCD2Processor.calculate_hash(row1)
    hash2 = CustomerSCD2Processor.calculate_hash(row2)
    hash3 = CustomerSCD2Processor.calculate_hash(row3)
    
    assert hash1 == hash2
    assert hash1 != hash3

@patch("scripts.scd2_customer.PostgresConnectionManager")
def test_scd2_customer_processing(mock_db_manager, config):
    mock_db = MagicMock()
    mock_db.__enter__.return_value = mock_db
    mock_db.cursor.fetchall.return_value = [(101, "existing_hash_diff")]
    mock_db_manager.return_value = mock_db
    
    processor = CustomerSCD2Processor(config)
    sample_df = pd.DataFrame([
        {'customer_id': 101, 'name': 'John Doe Updated', 'email': 'john@example.com', 'address': '456 St', 'city': 'NY'},
        {'customer_id': 102, 'name': 'Jane Smith', 'email': 'jane@example.com', 'address': '789 St', 'city': 'LA'}
    ])
    
    inserts, expires = processor.process_customer_scd2(sample_df)
    assert inserts == 2
    assert expires == 1

@patch("scripts.cdc_handler.PostgresConnectionManager")
def test_cdc_capture_changes(mock_db_manager, config):
    mock_db = MagicMock()
    mock_db.__enter__.return_value = mock_db
    mock_db.cursor.fetchall.return_value = [(1001,)]
    mock_db_manager.return_value = mock_db
    
    cdc = CDCProcessor(config)
    sample_orders = pd.DataFrame([
        {'order_id': 1001, 'customer_id': 101, 'product_id': 501},
        {'order_id': 1002, 'customer_id': 102, 'product_id': 502}
    ])
    
    summary = cdc.capture_changes("orders", sample_orders, key_column="order_id")
    assert summary["INSERT"] == 1
    assert summary["UPDATE"] == 1
