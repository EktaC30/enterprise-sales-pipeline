#  Enterprise Sales Data Pipeline

An end-to-end, enterprise-grade cloud data engineering pipeline that integrates continuous integration/deployment (CI/CD), web ingestion, cloud storage, and an automated multi-tier data warehouse.

---

##  Architecture Overview

```text
[ Git Push ] ──► [ GitHub Actions OIDC ] ──► [ Azure App Service (Flask/Gunicorn) ]
                                                       │
                                                 (CSV File Upload)
                                                       │
                                                       ▼
[ Snowflake Gold ] ◄── [ Silver Layer ] ◄── [ Bronze Layer ] ◄── [ Azure Blob Storage ]
  (Aggregations)        (CDC Cleaning)       (Snowpipe)            (Data Lake)
```

---

##  Tech Stack & Services

* **Application Layer:** Python 3.11, Flask, Gunicorn
* **CI/CD & Security:** GitHub Actions, Azure Active Directory / Entra ID (OIDC Passwordless Federated Auth)
* **Cloud Infrastructure:** Azure App Service, Azure Blob Storage (`salesfiles`), Azure PostgreSQL Flexible Server (`dba`)
* **Data Warehousing:** Snowflake (Medallion Architecture: Bronze → Silver → Gold)

---

##  Key Pipeline Features

1. **Zero-Trust CI/CD Deployment:** Passwordless OIDC authentication between GitHub Actions and Azure, eliminating hardcoded service principal client secrets.
2. **Automated Ingestion (Snowpipe):** Instant ingestion from Azure Blob Storage landing containers into Snowflake Bronze raw tables upon file landing.
3. **Change Data Capture (CDC):** Snowflake Streams and scheduled Tasks transform, clean, and deduplicate Bronze records into the Silver layer.
4. **Automated Analytical Summaries:** Downstream Snowflake DAG tasks aggregate sales metrics by category directly into Gold analytical summary tables.

---

##  Project Structure

```text
enterprise-sales-pipeline/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions OIDC CI/CD Workflow
├── app/
│   ├── templates/             # HTML Templates for CSV Upload Portal
│   ├── app.py                 # Flask Application Logic
│   └── etl.py                 # Operational ETL Processing Script
├── sql/
│   └── enterprise-sales.sql   # Snowflake Medallion Pipeline (DDL/DML)
├── .env.example               # Template for local environment variables
├── .gitignore                 # Excluded files & folders
├── Procfile                   # Process file for app runner
└── requirements.txt           # Python dependencies
```

---

##  Local Development & Setup

### Prerequisites
* Python 3.11+
* Git
* Azure CLI & PostgreSQL Client

### Environment Configuration
Copy `.env.example` to `.env` and configure your credentials:

```env
AZURE_STORAGE_CONNECTION_STRING=your_azure_storage_connection_string
CONTAINER_NAME=salesfiles
POSTGRES_HOST=your_postgres_host.postgres.database.azure.com
POSTGRES_DB=dba
POSTGRES_USER=your_postgres_admin
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_PORT=5432
```

### Installation & Local Run

```bash
# Clone repository
git clone https://github.com/EktaC30/enterprise-sales-pipeline.git
cd enterprise-sales-pipeline

# Install dependencies
pip install -r requirements.txt

# Run application locally
python app/app.py
```

---

##  Snowflake Pipeline Verification Queries

Once a CSV is uploaded via the Web App to Azure Blob Storage, verify data flow across the Medallion layers:

```sql
USE DATABASE ENTERPRISE_SALES_DB;

-- 1. Refresh Snowpipe & verify Bronze Layer (Raw Ingestion)
ALTER PIPE ENTERPRISE_SALES_DB.BRONZE.PIPE_RAW_SALES REFRESH;
SELECT * FROM ENTERPRISE_SALES_DB.BRONZE.RAW_SALES;

-- 2. Verify Silver Layer (Cleaned & Transformed Data)
SELECT * FROM ENTERPRISE_SALES_DB.SILVER.CLEAN_SALES;

-- 3. Verify Gold Layer (Business Aggregations)
SELECT * FROM ENTERPRISE_SALES_DB.GOLD.CATEGORY_SALES_SUMMARY;
```