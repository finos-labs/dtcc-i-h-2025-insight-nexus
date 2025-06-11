import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from one level above
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path)

# RDS connection configuration
RDS_HOST = os.getenv("RDS_HOST")
RDS_USER = os.getenv("RDS_USER")
RDS_PASSWORD = os.getenv("RDS_PASSWORD")
RDS_DB = os.getenv("RDS_DB")
ENGINE_URL = f"mysql+pymysql://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}/{RDS_DB}"
print(f"Connecting to RDS at {RDS_HOST}...")
# Define available datasets
DATASETS = {
    "prices": "prices",
    "indicators": "indicators",
    "financials": "financials",
    "corporate_actions": "corporate_actions"
}

for key, table in DATASETS.items():
    print(f"Registered dataset: {key} -> table: {table}")