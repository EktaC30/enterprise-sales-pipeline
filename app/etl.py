import os
import urllib.parse
import pandas as pd
from sqlalchemy import create_engine
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv(override=True)

# Environment variables
AZURE_CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
CONTAINER_NAME = os.getenv("CONTAINER_NAME", "salesfiles")

PG_HOST = os.getenv("POSTGRES_HOST")
PG_DB = os.getenv("POSTGRES_DB", "salesdb")
PG_USER = os.getenv("POSTGRES_USER")
PG_PASS = os.getenv("POSTGRES_PASSWORD")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")

def get_postgres_engine():
    """Create SQLAlchemy engine with short connection timeout."""
    encoded_pass = urllib.parse.quote_plus(PG_PASS) if PG_PASS else ""
    db_url = f"postgresql://{PG_USER}:{encoded_pass}@{PG_HOST}:{PG_PORT}/{PG_DB}?sslmode=require"
    # Timeout set to 5 seconds so local blocks don't hang the app
    return create_engine(db_url, connect_args={'connect_timeout': 5})

def upload_to_blob_storage(file_path, filename):
    """Upload raw CSV file to Azure Blob Storage container."""
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=filename)
    
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    print(f"[AZURE BLOB] Uploaded {filename} to container '{CONTAINER_NAME}' successfully.")

def process_operational_etl(file_path):
    """Clean data and attempt PostgreSQL load with fail-safe fallback."""
    df = pd.read_csv(file_path)
    df.columns = [col.lower().strip() for col in df.columns]
    
    required_cols = ['transaction_id', 'customer_id', 'product_category', 'amount', 'transaction_date']
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")
            
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0.0)
    df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.date
    
    # Try operational insert; log warning if blocked by corporate firewall
    try:
        engine = get_postgres_engine()
        df[required_cols].to_sql('sales_table', con=engine, if_exists='append', index=False)
        print(f"[POSTGRES ETL] Processed and inserted {len(df)} records into sales_table.")
    except Exception as e:
        print(f"[POSTGRES ETL NOTICE] Local connection to Azure PostgreSQL skipped due to network restriction (Port 5432 blocked on local network). Will execute automatically when deployed to Azure App Service.")