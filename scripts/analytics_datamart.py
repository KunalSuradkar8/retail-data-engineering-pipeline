import os
import sys
import logging
import pandas as pd
from typing import Dict, Any, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger
from utils.database import PostgresConnectionManager

class AnalyticsDataMart:
    """
    Enterprise Reporting & Analytics Data Mart Engine.
    Builds aggregated reporting tables (fact_daily_sales, customer_360)
    for BI Dashboards (PowerBI, Tableau) and Business Analysts.
    """
    def __init__(self, config_loader: ConfigLoader, logger: Optional[logging.Logger] = None):
        self.config = config_loader
        self.logger = logger or setup_logger("analytics_datamart")
        self.db_config = self.config.db_credentials

    def _init_datamart_tables(self, db: PostgresConnectionManager) -> None:
        """Initializes schema and tables for reporting data marts in PostgreSQL."""
        sql = """
        CREATE SCHEMA IF NOT EXISTS retail;
        
        -- Fact Table: Daily Sales Aggregations
        CREATE TABLE IF NOT EXISTS retail.fact_daily_sales (
            summary_date DATE PRIMARY KEY,
            total_orders INT,
            total_revenue NUMERIC(12, 2),
            avg_order_value NUMERIC(10, 2),
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Dimension Table: Customer 360 View
        CREATE TABLE IF NOT EXISTS retail.customer_360 (
            customer_id INT PRIMARY KEY,
            total_lifetime_orders INT,
            customer_lifetime_value NUMERIC(12, 2),
            avg_basket_size NUMERIC(10, 2),
            last_order_timestamp TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        db.cursor.execute(sql)

    def build_data_marts(self, sources_data: Dict[str, pd.DataFrame], transformed_orders: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculates and updates Data Mart tables in PostgreSQL.
        """
        self.logger.info("Building Analytics Data Marts (fact_daily_sales, customer_360)...")
        metrics = {}

        with PostgresConnectionManager(self.db_config, logger=self.logger) as db:
            self._init_datamart_tables(db)

            # 1. Update fact_daily_sales
            if not transformed_orders.empty and "total_amount" in transformed_orders.columns:
                today = pd.Timestamp.now().strftime("%Y-%m-%d")
                total_orders = len(transformed_orders)
                total_revenue = float(transformed_orders["total_amount"].sum())
                avg_order_val = float(transformed_orders["total_amount"].mean())

                db.cursor.execute(
                    """
                    INSERT INTO retail.fact_daily_sales (summary_date, total_orders, total_revenue, avg_order_value, last_updated)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (summary_date) DO UPDATE SET
                        total_orders = retail.fact_daily_sales.total_orders + EXCLUDED.total_orders,
                        total_revenue = retail.fact_daily_sales.total_revenue + EXCLUDED.total_revenue,
                        avg_order_value = (retail.fact_daily_sales.total_revenue + EXCLUDED.total_revenue) / (retail.fact_daily_sales.total_orders + EXCLUDED.total_orders),
                        last_updated = CURRENT_TIMESTAMP;
                    """,
                    (today, total_orders, total_revenue, avg_order_val)
                )
                self.logger.info(f"Updated 'retail.fact_daily_sales': Date={today}, Orders={total_orders}, Revenue=₹{total_revenue:,.2f}")
                metrics["today_revenue"] = total_revenue
                metrics["today_orders"] = total_orders

            # 2. Update customer_360
            if not transformed_orders.empty and "customer_id" in transformed_orders.columns:
                cust_grp = transformed_orders.groupby("customer_id").agg(
                    order_count=("order_id", "count"),
                    clv=("total_amount", "sum"),
                    avg_basket=("total_amount", "mean")
                ).reset_index()

                for _, row in cust_grp.iterrows():
                    db.cursor.execute(
                        """
                        INSERT INTO retail.customer_360 (customer_id, total_lifetime_orders, customer_lifetime_value, avg_basket_size, last_order_timestamp, last_updated)
                        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        ON CONFLICT (customer_id) DO UPDATE SET
                            total_lifetime_orders = retail.customer_360.total_lifetime_orders + EXCLUDED.total_lifetime_orders,
                            customer_lifetime_value = retail.customer_360.customer_lifetime_value + EXCLUDED.customer_lifetime_value,
                            avg_basket_size = (retail.customer_360.customer_lifetime_value + EXCLUDED.customer_lifetime_value) / (retail.customer_360.total_lifetime_orders + EXCLUDED.total_lifetime_orders),
                            last_order_timestamp = CURRENT_TIMESTAMP,
                            last_updated = CURRENT_TIMESTAMP;
                        """,
                        (int(row["customer_id"]), int(row["order_count"]), float(row["clv"]), float(row["avg_basket"]))
                    )
                self.logger.info(f"Updated 'retail.customer_360' for {len(cust_grp)} active customers.")
                metrics["active_customers_updated"] = len(cust_grp)

            self.logger.info("Successfully refreshed all Analytics Data Marts!")
            return metrics
