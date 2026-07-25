import logging
from typing import Dict, Any, List, Tuple
import psycopg2
from psycopg2 import extras
from utils.logger import setup_logger

class PostgresConnectionManager:
    """
    Context manager for PostgreSQL database connections and transactions.
    Automates connection opening, commit, rollback on failure, and safe resource cleanup.
    """
    def __init__(self, db_config: Dict[str, Any], logger: logging.Logger = None):
        self.db_config = db_config
        self.logger = logger or setup_logger("database_manager")
        self.connection = None
        self.cursor = None

    def __enter__(self):
        try:
            self.logger.info("Attempting to connect to PostgreSQL database...")
            self.connection = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"],
                password=self.db_config["password"]
            )
            self.cursor = self.connection.cursor()
            self.logger.info("PostgreSQL connection established successfully.")
            return self
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Database connection failed: {e}")
            raise e

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            if exc_type is not None:
                self.logger.warning(f"Exception encountered: {exc_val}. Rolling back database transaction.")
                try:
                    self.connection.rollback()
                    self.logger.info("Transaction rolled back successfully.")
                except Exception as rollback_err:
                    self.logger.error(f"Failed to rollback transaction: {rollback_err}")
            else:
                try:
                    self.connection.commit()
                    self.logger.info("Transaction committed successfully.")
                except Exception as commit_err:
                    self.logger.error(f"Failed to commit transaction: {commit_err}")
            
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            self.logger.info("Database connection and cursor closed safely.")

    def initialize_db(self) -> None:
        """
        Creates schema and orders table if not exists, and alters missing columns.
        """
        schema = self.db_config.get("schema", "retail")
        create_schema_query = f"CREATE SCHEMA IF NOT EXISTS {schema};"
        
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {schema}.orders (
            order_id INT PRIMARY KEY,
            customer_id INT NOT NULL,
            product_id INT NOT NULL,
            quantity INT NOT NULL,
            price NUMERIC(10, 2) NOT NULL,
            total_amount NUMERIC(12, 2) NOT NULL,
            load_timestamp TIMESTAMP WITH TIME ZONE NOT NULL
        );
        """
        
        alter_table_query = f"""
        ALTER TABLE {schema}.orders ADD COLUMN IF NOT EXISTS total_amount NUMERIC(12, 2);
        ALTER TABLE {schema}.orders ADD COLUMN IF NOT EXISTS load_timestamp TIMESTAMP WITH TIME ZONE;
        """
        try:
            self.logger.info(f"Initializing schema and table '{schema}.orders'...")
            self.cursor.execute(create_schema_query)
            self.cursor.execute(create_table_query)
            self.cursor.execute(alter_table_query)
            self.logger.info("Schema and table initialized successfully.")
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise e

    def initialize_dim_tables(self) -> None:
        """
        Creates customer SCD Type 2 dimension table and CDC audit table if not exists.
        """
        schema = self.db_config.get("schema", "retail")
        
        create_dim_customer_query = f"""
        CREATE TABLE IF NOT EXISTS {schema}.dim_customer (
            customer_sk SERIAL PRIMARY KEY,
            customer_id INT NOT NULL,
            name VARCHAR(100),
            email VARCHAR(100),
            address VARCHAR(200),
            city VARCHAR(50),
            hash_diff VARCHAR(32) NOT NULL,
            effective_start_date TIMESTAMP WITH TIME ZONE NOT NULL,
            effective_end_date TIMESTAMP WITH TIME ZONE,
            is_current BOOLEAN NOT NULL DEFAULT TRUE
        );
        CREATE INDEX IF NOT EXISTS idx_dim_customer_id ON {schema}.dim_customer(customer_id);
        """
        
        create_cdc_audit_query = f"""
        CREATE TABLE IF NOT EXISTS {schema}.cdc_audit_log (
            change_id SERIAL PRIMARY KEY,
            table_name VARCHAR(50) NOT NULL,
            record_id INT NOT NULL,
            action_type VARCHAR(10) NOT NULL,
            changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        );
        """
        try:
            self.logger.info(f"Initializing dim_customer and cdc_audit_log in schema '{schema}'...")
            self.cursor.execute(create_dim_customer_query)
            self.cursor.execute(create_cdc_audit_query)
            self.logger.info("Dimension and CDC tables initialized successfully.")
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Dimension tables initialization failed: {e}")
            raise e

    def execute_query(self, query: str, params: Tuple = None) -> None:
        """
        Execute a single SQL query.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.logger.info("Query executed successfully.")
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Query execution failed: {e}")
            raise e    

    def fetch_all(self, query: str, params: Tuple = None) -> List[Tuple]:
        """
        Execute a query and fetch all results.
        """
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Query execution failed: {e}")
            raise e    

    def insert_bulk(self, query: str, data: List[Tuple]) -> int:
        """
        High-performance bulk insertion using psycopg2.extras.execute_values.
        """
        if not data:
            self.logger.warning("No data provided for bulk insertion.")
            return 0

        try:
            self.logger.info(f"Executing bulk insertion for {len(data)} records...")
            extras.execute_values(self.cursor, query, data)
            rows_inserted = len(data)
            self.logger.info(f"Bulk insertion of {rows_inserted} records completed successfully.")
            return rows_inserted
        except psycopg2.DatabaseError as e:
            self.logger.error(f"Bulk insertion failed: {e}")
            raise e

