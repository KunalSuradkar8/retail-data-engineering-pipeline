import os
import sys
import json
import logging
import smtplib
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from typing import Dict, Any, Optional, List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger

class SlackNotifier:
    """
    Sends formatted Slack Webhook alerts for pipeline execution events.
    """
    def __init__(self, webhook_url: Optional[str] = None, logger: Optional[logging.Logger] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.logger = logger or setup_logger("slack_notifier")

    def send_alert(self, title: str, message: str, status: str = "INFO", details: Optional[Dict[str, Any]] = None) -> bool:
        """
        Sends formatted Slack card alert. Status can be 'SUCCESS', 'WARNING', 'FAILURE', 'INFO'.
        """
        if not self.webhook_url or "hooks.slack.com" not in self.webhook_url:
            self.logger.info(f"[Slack Notifier - Fallback Log] [{status}] {title}: {message}")
            return False

        color_map = {
            "SUCCESS": "#10b981",  # Green
            "WARNING": "#f59e0b",  # Yellow
            "FAILURE": "#ef4444",  # Red
            "INFO": "#3b82f6"      # Blue
        }

        fields = []
        if details:
            for k, v in details.items():
                fields.append({"title": str(k), "value": str(v), "short": True})

        payload = {
            "attachments": [
                {
                    "color": color_map.get(status, "#3b82f6"),
                    "title": f"🚨 Retail Pipeline Alert: {title}",
                    "text": message,
                    "fields": fields,
                    "footer": "Retail Data Engineering Pipeline",
                    "ts": int(os.path.getmtime(__file__)) if os.path.exists(__file__) else None
                }
            ]
        }

        try:
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as resp:
                if resp.status == 200:
                    self.logger.info(f"Slack alert '{title}' sent successfully.")
                    return True
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
        return False

class EmailNotifier:
    """
    Sends SMTP Email alerts and rich HTML executive reports for pipeline execution events.
    """
    def __init__(self, email_config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        self.config = email_config if email_config is not None else {}
        self.logger = logger or setup_logger("email_notifier")
        self.smtp_server = self.config.get("smtp_server") or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(self.config.get("smtp_port") or os.getenv("SMTP_PORT", 587))
        
        self.sender_email = self.config.get("sender_email") or os.getenv("SENDER_EMAIL")
        self.sender_password = self.config.get("sender_password") or os.getenv("SENDER_PASSWORD")

    def send_email(self, recipient_email: str, subject: str, body: str, attachment_paths: Optional[List[str]] = None) -> bool:
        """
        Sends plain text or rich HTML email via SMTP with optional file attachments.
        """
        if not self.sender_email or not self.sender_password:
            self.logger.info(f"[Email Notifier - Fallback Log] Subject: {subject} | Body: {body[:100]}...")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html" if "<html>" in body.lower() else "plain"))

            if attachment_paths:
                for path in attachment_paths:
                    if os.path.exists(path):
                        with open(path, "rb") as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(path))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(path)}"'
                            msg.attach(part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            self.logger.info(f"Email '{subject}' sent successfully to {recipient_email}.")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False

class PipelineAlertNotifier:
    """
    Unified Pipeline Notification & Alerting System.
    Orchestrates Slack and Rich HTML Email alerting safely without crashing execution.
    """
    def __init__(self, config_loader: ConfigLoader, logger: Optional[logging.Logger] = None):
        self.config = config_loader
        self.logger = logger or setup_logger("pipeline_notifier")
        
        slack_url = self.config.get("notifications.slack_webhook_url")
        email_cfg = self.config.get("notifications.email")
        
        self.slack = SlackNotifier(webhook_url=slack_url, logger=self.logger)
        self.email = EmailNotifier(email_config=email_cfg, logger=self.logger)

    def _generate_html_report(self, title: str, status: str, message: str, details: Optional[Dict[str, Any]] = None) -> str:
        """Generates an Enterprise HTML Email Template."""
        theme_color = "#10b981" if status == "SUCCESS" else "#ef4444"
        badge_text = "PASSED" if status == "SUCCESS" else "FAILED"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        details_rows = ""
        if details:
            for k, v in details.items():
                details_rows += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #475569;">{k}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; color: #1e293b;">{v}</td>
                </tr>
                """

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; }}
                .container {{ max-width: 650px; background: #ffffff; margin: 0 auto; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
                .header {{ background-color: {theme_color}; color: #ffffff; padding: 24px; text-align: left; }}
                .header h2 {{ margin: 0; font-size: 22px; font-weight: 600; }}
                .badge {{ background: rgba(255, 255, 255, 0.2); padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: bold; float: right; }}
                .content {{ padding: 24px; }}
                .summary-card {{ background: #f1f5f9; padding: 16px; border-left: 4px solid {theme_color}; border-radius: 4px; margin-bottom: 20px; }}
                .table-title {{ font-size: 16px; font-weight: bold; margin-bottom: 10px; color: #0f172a; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
                .footer {{ background: #f1f5f9; padding: 16px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <span class="badge">{badge_text}</span>
                    <h2>📊 Enterprise Retail ETL Pipeline Report</h2>
                </div>
                <div class="content">
                    <div class="summary-card">
                        <strong>Status:</strong> {title}<br>
                        <span style="color: #475569; font-size: 14px;">{message}</span>
                    </div>
                    <div class="table-title">📈 Execution Details & Metrics</div>
                    <table>
                        <tr>
                            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: 600; color: #475569;">Execution Time</td>
                            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; color: #1e293b;">{timestamp}</td>
                        </tr>
                        {details_rows}
                    </table>
                </div>
                <div class="footer">
                    Automated Alert generated by <strong>Retail Data Engineering Engine</strong>.<br>
                    Confidential & Internal Operations Monitoring.
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def notify_pipeline_success(self, job_name: str, rows_loaded: int, details: Optional[Dict[str, Any]] = None, attachment_paths: Optional[List[str]] = None):
        """Sends success alert across Slack & Rich HTML Email."""
        title = f"{job_name} Completed Successfully"
        message = f"ETL Job '{job_name}' completed cleanly. Total rows loaded into target DB: {rows_loaded}."
        
        info_details = {"Rows Loaded": rows_loaded}
        if details:
            info_details.update(details)

        self.logger.info(f"[SUCCESS ALERT] {title} - {message}")
        self.slack.send_alert(title, message, status="SUCCESS", details=info_details)

        recipient = self.config.get("notifications.email.recipient_email")
        if recipient:
            html_body = self._generate_html_report(title, "SUCCESS", message, details=info_details)
            self.email.send_email(recipient, f"🟢 [Retail ETL Report] SUCCESS: {job_name}", html_body, attachment_paths=attachment_paths)

    def notify_pipeline_failure(self, job_name: str, error_msg: str, failed_step: str = "Unknown", attachment_paths: Optional[List[str]] = None):
        """Sends failure alert across Slack & Rich HTML Email."""
        title = f"{job_name} FAILED at step '{failed_step}'"
        message = f"Critical Failure in ETL Job '{job_name}'. Error: {error_msg}"
        
        details = {
            "Failed Step": failed_step,
            "Error Message": error_msg
        }

        self.logger.error(f"[FAILURE ALERT] {title} - {message}")
        self.slack.send_alert(title, message, status="FAILURE", details=details)

        recipient = self.config.get("notifications.email.recipient_email")
        if recipient:
            html_body = self._generate_html_report(title, "FAILURE", message, details=details)
            self.email.send_email(recipient, f"🔴 [Retail ETL Report] FAILURE: {job_name}", html_body, attachment_paths=attachment_paths)
