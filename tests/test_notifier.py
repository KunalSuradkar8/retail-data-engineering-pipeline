import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from unittest.mock import MagicMock, patch
from utils.config_loader import ConfigLoader
from utils.notifier import SlackNotifier, EmailNotifier, PipelineAlertNotifier

@pytest.fixture
def config():
    return ConfigLoader()

def test_slack_notifier_fallback(config):
    notifier = SlackNotifier(webhook_url=None)
    result = notifier.send_alert("Test Alert", "Testing fallback mode", status="INFO")
    assert result is False

@patch.dict(os.environ, {"SENDER_EMAIL": "", "SENDER_PASSWORD": ""})
def test_email_notifier_fallback(config):
    notifier = EmailNotifier(email_config={})
    result = notifier.send_email("test@example.com", "Test Subject", "Test Body")
    assert result is False

@patch("utils.notifier.SlackNotifier.send_alert")
def test_pipeline_alert_notifier_success(mock_slack_alert, config):
    mock_slack_alert.return_value = True
    notifier = PipelineAlertNotifier(config)
    
    notifier.notify_pipeline_success("Test_Job", rows_loaded=100)
    mock_slack_alert.assert_called_once()
    assert mock_slack_alert.call_args[0][0] == "Test_Job Completed Successfully"

@patch("utils.notifier.SlackNotifier.send_alert")
def test_pipeline_alert_notifier_failure(mock_slack_alert, config):
    mock_slack_alert.return_value = True
    notifier = PipelineAlertNotifier(config)
    
    notifier.notify_pipeline_failure("Test_Job", "Database Connection Refused", failed_step="DB Load")
    mock_slack_alert.assert_called_once()
    assert "FAILED" in mock_slack_alert.call_args[0][0]
