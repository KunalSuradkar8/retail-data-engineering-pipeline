import os
import sys

# Test execution साठी प्रोजेक्ट रूट sys.path मध्ये जोडतो
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
import pandas as pd
from utils.config_loader import ConfigLoader
from scripts.extract import DataExtractor
from scripts.validation import DataValidator
from scripts.transform import DataTransformer

@pytest.fixture
def config():
    """ConfigLoader ची फिक्स्चर चाचणीसाठी इनिशियलाईझ करतो."""
    return ConfigLoader()

def test_config_loader_singleton(config):
    """ConfigLoader Singleton Pattern चे पालन करतो का ते तपासणे."""
    config2 = ConfigLoader()
    assert config is config2
    assert "host" in config.db_credentials

def test_data_validation_quality_rules(config):
    """DataValidator योग्य डेटा आणि अयोग्य डेटा अचूक विभक्त करतो का ते तपासणे."""
    validator = DataValidator(config)
    sample_data = {
        "order_id": [1, 2, 3],
        "customer_id": [101, 102, 103],
        "product_id": [501, 502, 503],
        "quantity": [2, -1, 3],        # Order 2 has invalid negative quantity
        "price": [100.0, 50.0, -20.0]   # Order 3 has invalid negative price
    }
    df = pd.DataFrame(sample_data)
    good_df, bad_df = validator.validate(df)

    assert len(good_df) == 1
    assert len(bad_df) == 2
    assert good_df.iloc[0]["order_id"] == 1

def test_data_transformation_calculations(config):
    """DataTransformer 'total_amount' आणि 'load_timestamp' अचूक जोडतो का ते तपासणे."""
    transformer = DataTransformer(config)
    valid_data = {
        "order_id": [1],
        "customer_id": [101],
        "product_id": [501],
        "quantity": [4],
        "price": [25.0]
    }
    df = pd.DataFrame(valid_data)
    transformed_df = transformer.transform(df)

    assert "total_amount" in transformed_df.columns
    assert "load_timestamp" in transformed_df.columns
    assert transformed_df.iloc[0]["total_amount"] == 100.0  # 4 * 25.0 = 100.0

def test_extractor_empty_directory_handling(config, tmp_path):
    """रिकामा फोल्डर असल्‍यास DataExtractor सुरक्षितपणे हँडल करतो का ते तपासणे."""
    extractor = DataExtractor(config)
    extractor.raw_dir = str(tmp_path)  # रिकामा तात्पुरता फोल्डर वापरतो
    
    df, file_path = extractor.extract()
    assert df is None
    assert file_path is None
