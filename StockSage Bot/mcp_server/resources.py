from pandas.api.types import is_numeric_dtype, is_datetime64_any_dtype
from mcp.server.fastmcp import FastMCP
import pandas as pd
from config import DATASETS
from db import engine
from datetime import datetime
import json

# Current date for metadata, dynamically set when script runs
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")

def fetch_metadata():
    try:
        metadata = {
            "tables": {},
            "date_format": "YYYY-MM-DD",
            "current_date": CURRENT_DATE
        }
        with engine.connect() as connection:
            with connection.begin():
                for dataset, table in DATASETS.items():
                    df_sample = pd.read_sql(f"SELECT * FROM {table} LIMIT 100", connection)
                    columns = list(df_sample.columns)

                    categorical = {}
                    for col in columns:
                        # Skip known date columns
                        if col.lower() in ['date', 'action_date']:
                            continue
                        # Skip datetime or numeric types
                        if is_datetime64_any_dtype(df_sample[col]) or is_numeric_dtype(df_sample[col]):
                            continue
                        # Explicit column exclusions
                        if (table == 'corporate_actions' and col == 'details') or \
                           (table == 'indicators' and col == 'sma_200'):
                            continue

                        # Fetch unique values
                        query = f"SELECT DISTINCT {col} FROM {table} LIMIT 100"
                        df_unique = pd.read_sql(query, connection)
                        categorical[col] = df_unique[col].dropna().unique().tolist()

                    metadata["tables"][dataset] = {
                        "columns": columns,
                        "categorical_values": categorical
                    }
        return metadata
    except Exception as e:
        print(f"Error fetching metadata: {str(e)}")
        return {"error": f"Failed to fetch metadata: {str(e)}"}

# Cache metadata at startup
CACHED_METADATA = fetch_metadata()
# Save to a local file
with open('meta_data.json', 'w') as f:
    json.dump(CACHED_METADATA, f, indent=2)

def register_resources(mcp: FastMCP):
    # Resource: Expose table contents for a given stock symbol
    @mcp.resource("stock://{dataset}/{symbol}")
    def get_stock_data(dataset: str, symbol: str) -> str:
        """
        Retrieve stock data for a specific dataset and symbol from the database.
    
        Parameters:
            dataset (str): The dataset to query (e.g., 'prices', 'indicators', 'financials', 'corporate_actions').
            symbol (str): The stock symbol to filter the data (e.g., 'AAPL').
    
        Returns:
            str: JSON string containing the queried data in 'records' orientation, or an error message if the dataset
                 is invalid or no data is found.
        """
        print(f"Accessing resource stock://{dataset}/{symbol}")  
        if dataset not in DATASETS:
            return f"Error: Dataset {dataset} not found. Available datasets: {list(DATASETS.keys())}"
        try:
            table = DATASETS[dataset]
            with engine.connect() as connection:
                with connection.begin():  # Start a transaction
                    query = f"SELECT * FROM {table} WHERE symbol = %s"
                    df = pd.read_sql(query, engine, params=(symbol,))
                    if df.empty:
                        return f"Error: No data found for symbol {symbol} in {dataset}"
                    return df.to_json(orient="records")
        except Exception as e:
            return f"Error reading {dataset} for {symbol}: {str(e)}"