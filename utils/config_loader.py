import os
import json
from typing import Any, Dict
from dotenv import load_dotenv

class ConfigLoader:
    """
    Singleton Pattern: Loads JSON configuration and .env file once into memory.
    """
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls, config_path: str = "config/config.json"):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_config(config_path)
        return cls._instance

    def _load_config(self, config_path: str) -> None:
        if not os.path.isabs(config_path):
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            config_path = os.path.join(project_root, config_path)

        load_dotenv()

        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in configuration file: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves nested config key using dot notation. Example: config.get("database.target_table")
        """
        keys = key.split(".")
        value: Any = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    @property
    def config(self) -> Dict[str, Any]:
        return self._config

    @property
    def db_credentials(self) -> Dict[str, Any]:
        return {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", 5432)),
            "database": os.getenv("DB_NAME", "retail_db"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "schema": os.getenv("DB_SCHEMA", "retail")
        }
