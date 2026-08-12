import os
import pandas as pd
from sqlalchemy import create_engine
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

# Environment variables
AZURE_CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "salesfiles")

PG_HOST = os.getenv("POSTGRES_HOST")
PG_DB = os.getenv("POSTGRES_DB", "salesdb")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")

def get_postgres_engine():
    """Create SQLAlchemy engine for Azure PostgreSQL."""
    db_url = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
    return create_engine(db_url)

def upload_to_blob_storage(file_path, filename):
    """Upload raw CSV file to Azure Blob Storage container."""
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=filename)
    
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    print(f"[AZURE BLOB] Uploaded {filename} to container '{CONTAINER_NAME}' successfully.")

def process_operational_etl(file_path):
    """Clean data using Pandas and load into Azure PostgreSQL."""
    # 1. Read Data
    df = pd.read_csv(file_path)
    
    # 2. Clean & Standardize
    df.columns = [col.lower().strip() for col in df.columns]
    
    required_cols = ['transaction_id', 'customer_id', 'product_category', 'amount', 'transaction_date']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
            
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
    df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.date
    
    # 3. Load into PostgreSQL
    engine = get_postgres_engine()
    df[required_cols].to_sql('sales_table', con=engine, if_exists='append', index=False)
    print(f"[POSTGRES ETL] Processed and inserted {len(df)} records into sales_table.")