import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
import pandas as pd
from utils.config_loader import ConfigLoader
from scripts.multi_source_extractor import MultiSourceExtractor

@pytest.fixture
def config():
    return ConfigLoader()

def test_multi_source_csv_extraction(config):
    extractor = MultiSourceExtractor(config)
    df = extractor.extract_from_csv()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "order_id" in df.columns

def test_multi_source_api_json_extraction(config):
    extractor = MultiSourceExtractor(config)
    df = extractor.extract_from_api_json()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "transaction_id" in df.columns

def test_multi_source_sqlite_extraction(config):
    extractor = MultiSourceExtractor(config)
    df = extractor.extract_from_sqlite()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "customer_id" in df.columns

def test_multi_source_clickstream_json_extraction(config):
    extractor = MultiSourceExtractor(config)
    df = extractor.extract_from_clickstream_json()
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "session_id" in df.columns

def test_multi_source_all_sources(config):
    extractor = MultiSourceExtractor(config)
    results = extractor.extract_all_sources()
    assert isinstance(results, dict)
    assert "csv_orders" in results
    assert "api_payments" in results
    assert "sqlite_customers" in results
    assert "postgresql_orders" in results
    assert "clickstream_events" in results
