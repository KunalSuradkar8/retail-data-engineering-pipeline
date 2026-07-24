# 🛒 Retail Data Engineering ETL Pipeline

A production-ready, modular Data Engineering ETL (Extract, Validate, Transform, Load) pipeline built in Python 3.11 and PostgreSQL for retail order processing.

---

## 🏗️ Pipeline Architecture & Data Flow

```text
+------------------+
|   Raw CSV Files  | (data/raw/)
+--------+---------+
         |
         v
+------------------+
|   Extract Step   | (scripts/extract.py)
+--------+---------+
         |
         v
+------------------+
|  Validation Step | (scripts/validation.py)
+--------+---------+
         |
         +----------------------------------+
         |                                  |
         v (Good Records)                   v (Bad Records)
+------------------+              +------------------+
|  Transform Step  |              | Persist Bad Data | (data/bad_records/bad_orders.csv)
+--------+---------+              +------------------+
         |
         v
+------------------+
|    Load Step     | (scripts/load.py)
|  (PostgreSQL)    | (target: retail.orders - Idempotent UPSERT)
+--------+---------+
         |
         v
+------------------+
|   Archive File   | (data/archive/)
+------------------+
```

---

## ⚙️ Design Patterns & Best Practices

1. **SOLID Principles**: Single Responsibility modules for Extraction, Validation, Transformation, and Loading.
2. **Context Manager Pattern**: `PostgresConnectionManager` automates commits, rollbacks, and connection closing.
3. **Singleton Pattern**: `ConfigLoader` reads configuration files once into memory.
4. **Idempotent Loading**: Database insert uses PostgreSQL `UPSERT` (`ON CONFLICT (order_id) DO UPDATE`).
5. **Data Quality & Lineage**: Persists invalid records to `data/bad_records/bad_orders.csv` with explicit `rejection_reason`.
6. **Automated CI/CD**: Integrated GitHub Actions workflow for running `pytest` unit tests on every push.

---

## 🚀 Quick Start Guide

### 1. Clone & Install Dependencies
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Database (.env)
Create a `.env` file in the root directory:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_SCHEMA=retail
```

### 3. Run Pipeline & Analytics
```bash
# Execute Main ETL Pipeline
python scripts/main.py

# Generate Business Analytics Report
python scripts/analytics.py

# Run Automated Unit Tests
pytest -v
```

### 4. Run with Docker Containers
```bash
# Build and start all services (PostgreSQL + ETL Pipeline)
docker-compose up --build
```

