from ta.trend import SMAIndicator, EMAIndicator, MACD, ADXIndicator
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.trend import CCIIndicator
import pandas as pd
import yfinance as yf
from datetime import timedelta, datetime
import json
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from config import DATASETS
from db import engine
from mcp.server.fastmcp import FastMCP
import wikipediaapi

def register_tools(mcp: FastMCP):
    # Tool: Query data with a simple filter
    @mcp.tool()
    def query_stock_data(dataset: str, symbol: str, column: str, value: str) -> str:
        """
        Query stock data with a filter on a specific column and value for a given dataset and symbol.

        Parameters:
            dataset (str): The dataset to query (e.g., 'prices', 'indicators', 'financials', 'corporate_actions').
            symbol (str): The stock symbol to filter the data (e.g., 'AAPL').
            column (str): The column name to apply the filter on.
            value (str): The value to search for in the specified column (using LIKE operator with wildcards).

        Returns:
            str: JSON string containing the filtered data in 'records' orientation, or an error message if the dataset,
                 column, or data is invalid or not found.
        """
        print(f"Executing tool query_stock_data: dataset={dataset}, symbol={symbol}, column={column}, value={value}")  # Debug
        if dataset not in DATASETS:
            return f"Error: Dataset {dataset} not found. Available datasets: {list(DATASETS.keys())}"
        try:
            table = DATASETS[dataset]
            with engine.connect() as connection:
                with connection.begin():  # Start a transaction
                    # Get column names to validate
                    df_columns = pd.read_sql(f"SELECT * FROM {table} LIMIT 1", engine)
                    if column not in df_columns.columns:
                        return f"Error: Column {column} not found in {dataset}"
                    query = f"SELECT * FROM {table} WHERE symbol = %s AND {column} LIKE %s"
                    df = pd.read_sql(query, engine, params=(symbol, f"%{value}%"))
                    if df.empty:
                        return f"Error: No data found for symbol {symbol} in {dataset} with {column} containing {value}"
                    return df.to_json(orient="records", date_format="iso")
        except Exception as e:
            return f"Error querying {dataset} for {symbol}: {str(e)}"

    # Tool: Get summary statistics
    @mcp.tool()
    def get_stock_summary(dataset: str, symbol: str) -> str:
        """
        Generate summary statistics for numeric columns in the specified dataset for a given stock symbol.

        Parameters:
            dataset (str): The dataset to query (e.g., 'prices', 'indicators', 'financials', 'corporate_actions').
            symbol (str): The stock symbol to filter the data (e.g., 'AAPL').

        Returns:
            str: JSON string containing summary statistics (e.g., mean, std, min, max) for numeric columns in 'records'
                 orientation, or an error message if the dataset is invalid, no data is found, or no numeric columns exist.
        """
        print(f"Executing tool get_stock_summary: dataset={dataset}, symbol={symbol}")  # Debug
        if dataset not in DATASETS:
            return f"Error: Dataset {dataset} not found. Available datasets: {list(DATASETS.keys())}"
        try:
            table = DATASETS[dataset]
            with engine.connect() as connection:
                with connection.begin():  # Start a transaction
                    query = f"SELECT * FROM {table} WHERE symbol = %s"
                    df = pd.read_sql(query, engine, params=(symbol,))
                    print(df)
                    if df.empty:
                        return f"Error: No data found for symbol {symbol} in {dataset}"
                    # Exclude non-numeric columns for summary
                    numeric_df = df.select_dtypes(include=['float64', 'int64'])
                    if numeric_df.empty:
                        return f"Error: No numeric columns to summarize for {symbol} in {dataset}"
                    return numeric_df.describe().to_json(orient="records", date_format="iso")
        except Exception as e:
            print(f"Error in get_stock_summary: {str(e)}")  # Debug
            return f"Error summarizing {dataset} for {symbol}: {str(e)}"

    # Tool: Execute raw SQL query
    @mcp.tool()
    def execute_sql_query(query: str) -> str:
        """
        Execute a raw SQL query against the connected database.

        Parameters:
            query (str): A valid SQL SELECT query to be executed.

        Returns:
            str: JSON string of the query result in 'records' format, or an error message.
        """
        print(f"Executing tool execute_sql_query: {query}")  # Debug
        try:
            if not query.strip().lower().startswith("select"):
                return "Error: Only SELECT queries are allowed."
            with engine.connect() as connection:
                with connection.begin():
                    df = pd.read_sql(query, connection)
                    if df.empty:
                        return "Notice: Query executed successfully, but no rows were returned."
                    return df.to_json(orient="records", date_format="iso")
        except Exception as e:
            print(f"SQL execution error: {str(e)}")  # Debug
            return f"Error executing query: {str(e)}"


    # Tool: Fetch price data for out-of-DB symbols using yfinance
    @mcp.tool()
    def fetch_external_price_data(symbol: str, start_date: str, end_date: str) -> str:
        """
        Fetch historical price data for symbols that are not in the database using yfinance.
    
        Parameters:
            symbol (str): The stock ticker symbol (e.g., 'GOOG', 'MSFT').
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format (inclusive).
    
        Returns:
            str: JSON string of the historical price data or an error message.
        """
        print(f"Fetching external price data: symbol={symbol}, start_date={start_date}, end_date={end_date}")
        
        try:
            # Make end_date inclusive
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            end_date_exclusive = end_dt.strftime("%Y-%m-%d")
    
            df = yf.download(symbol, start=start_date, end=end_date_exclusive)
            if df.empty:
                return f"Error: No data found for {symbol} between {start_date} and {end_date}."
    
            df.reset_index(inplace=True)
            df.rename(columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume"
            }, inplace=True)
            df = df[["date", "open", "high", "low", "close", "volume"]]
            return df.to_json(orient="records", date_format="iso")
        
        except Exception as e:
            return f"Error fetching external price data for {symbol}: {str(e)}"



    # Tool: Fetch and compute indicators for external symbols
    @mcp.tool()
    def fetch_external_indicators(symbol: str, start_date: str, end_date: str) -> str:
        """
        Fetch price data and calculate technical indicators("sma_20", "sma_50", "sma_200", "ema_12", "ema_26", 
                     "rsi_14", "macd", "macd_signal", "macd_hist", "bb_upper", "bb_middle", 
                     "bb_lower", "adx_14", "cci_20", "stochastic_k", "stochastic_d", 
                     "williams_r") for external symbols not in the database.
    
        Parameters:
            symbol (str): Stock ticker (e.g., 'GOOG').
            start_date (str): Start date in 'YYYY-MM-DD' format.
            end_date (str): End date in 'YYYY-MM-DD' format (inclusive).
    
        Returns:
            str: JSON string of technical indicators or an error message.
    
        Note:
            The difference between start_date and end_date should be **at least 50 days**.
            If the range is shorter, indicator computation may fail due to insufficient data.
        """
        try:
            print(f"Fetching indicators: symbol={symbol}, start={start_date}, end={end_date}")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            end_date_exclusive = end_dt.strftime("%Y-%m-%d")
        
            # Disable auto_adjust to avoid multi-index issues
            df = yf.download(symbol, start=start_date, end=end_date_exclusive, auto_adjust=False)
            if df.empty:
                return f"Error: No data found for {symbol} in given date range."
        
            # Flatten multi-level columns if needed
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0].lower() for col in df.columns]
            else:
                df.columns = [col.lower() for col in df.columns]
        
            df.reset_index(inplace=True)
            df["symbol"] = symbol
            df.rename(columns={'Date':'date'}, inplace=True)
        
            # Ensure required columns are in correct format
            df["date"] = pd.to_datetime(df["date"])
            df["close"] = df["close"].astype(float)
            df["high"] = df["high"].astype(float)
            df["low"] = df["low"].astype(float)
        
            # Compute indicators
            df["sma_20"] = SMAIndicator(close=df["close"], window=20).sma_indicator().astype(float)
            df["sma_50"] = SMAIndicator(close=df["close"], window=50).sma_indicator().astype(float)
            df["sma_200"] = SMAIndicator(close=df["close"], window=200).sma_indicator().astype(float)
        
            df["ema_12"] = EMAIndicator(close=df["close"], window=12).ema_indicator().astype(float)
            df["ema_26"] = EMAIndicator(close=df["close"], window=26).ema_indicator().astype(float)
        
            df["rsi_14"] = RSIIndicator(close=df["close"], window=14).rsi().astype(float)
        
            macd = MACD(close=df["close"])
            df["macd"] = macd.macd().astype(float)
            df["macd_signal"] = macd.macd_signal().astype(float)
            df["macd_hist"] = macd.macd_diff().astype(float)
        
            bb = BollingerBands(close=df["close"], window=20)
            df["bb_upper"] = bb.bollinger_hband().astype(float)
            df["bb_middle"] = bb.bollinger_mavg().astype(float)
            df["bb_lower"] = bb.bollinger_lband().astype(float)
        
            df["adx_14"] = ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=14).adx().astype(float)
            df["cci_20"] = CCIIndicator(high=df["high"], low=df["low"], close=df["close"], window=20).cci().astype(float)
        
            stoch = StochasticOscillator(high=df["high"], low=df["low"], close=df["close"], window=14, smooth_window=3)
            df["stochastic_k"] = stoch.stoch().astype(float)
            df["stochastic_d"] = stoch.stoch_signal().astype(float)
        
            df["williams_r"] = WilliamsRIndicator(high=df["high"], low=df["low"], close=df["close"], lbp=14).williams_r().astype(float)
        
            result = df[["symbol", "date", "sma_20", "sma_50", "sma_200", "ema_12", "ema_26", 
                         "rsi_14", "macd", "macd_signal", "macd_hist", "bb_upper", "bb_middle", 
                         "bb_lower", "adx_14", "cci_20", "stochastic_k", "stochastic_d", 
                         "williams_r"]]
            
            return result.to_json(orient="records", date_format="iso")

        except Exception as e:
            return f"Error fetching indicators for {symbol}: {str(e)}"


    # Tool: List available stock symbols
    @mcp.tool()
    def list_stock_symbols() -> str:
        """
        Retrieve a list of distinct stock symbols available in the 'prices' table.

        Returns:
            str: JSON string containing a list of stock symbols in 'records' orientation, or an error message if no symbols
                 are found or an error occurs during query execution.
        """
        print("Executing tool list_stock_symbols")  # Debug
        try:
            with engine.connect() as connection:
                with connection.begin():  # Start a transaction
                    query = "SELECT DISTINCT symbol FROM prices"
                    df = pd.read_sql(query, connection)  # Use connection directly
                    print(df)
                    if df.empty:
                        return "Error: No stock symbols found in the database"
                    return df["symbol"].to_json(orient="records", date_format="iso")
        except Exception as e:
            print(f"Error in list_stock_symbols: {str(e)}")  # Debug
            return f"Error listing stock symbols: {str(e)}"


    # Tool: Compare stock metrics across symbols
    @mcp.tool()
    def compare_stock_metrics(dataset: str, symbols: str, column: str, start_date: str, end_date: str) -> str:
        """
        Compare a specific column across multiple stock symbols for a given dataset and date range.
        Parameters:
            dataset (str): The dataset to query (e.g., 'prices', 'indicators', 'financials').
            symbols (str): Comma-separated list of stock symbols (e.g., 'AAPL,MSFT').
            column (str): The column name to compare (e.g., 'close', 'rsi_14', 'revenue').
            start_date (str): Start date for the range (e.g., '2024-01-01').
            end_date (str): End date for the range (e.g., '2024-12-31').
        Returns:
            str: JSON string containing the compared data in 'records' orientation, or an error message if invalid.
        """
        print(f"Executing tool compare_stock_metrics: dataset={dataset}, symbols={symbols}, column={column}, start_date={start_date}, end_date={end_date}")  # Debug
        if dataset not in DATASETS:
            return f"Error: Dataset {dataset} not found. Available datasets: {list(DATASETS.keys())}"
        try:
            table = DATASETS[dataset]
            symbol_list = symbols.split(',')
            with engine.connect() as connection:
                with connection.begin():
                    df_columns = pd.read_sql(f"SELECT * FROM {table} LIMIT 1", engine)
                    if column not in df_columns.columns:
                        return f"Error: Column {column} not found in {dataset}"
                    query = f"SELECT symbol, date, {column} FROM {table} WHERE symbol IN %s AND date BETWEEN %s AND %s"
                    df = pd.read_sql(query, engine, params=(tuple(symbol_list), start_date, end_date))
                    if df.empty:
                        return f"Error: No data found for symbols {symbols} in {dataset} from {start_date} to {end_date}"
                    return df.to_json(orient="records", date_format="iso")
        except Exception as e:
            return f"Error comparing {dataset} for {symbols}: {str(e)}"

    # Tool: Fetch real-time price data
    @mcp.tool()
    def fetch_realtime_price(symbol: str) -> str:
        """
        Fetch real-time or recent stock price data for a given symbol using yfinance.
        Parameters:
            symbol (str): The stock symbol to fetch data for (e.g., 'AAPL').
        Returns:
            str: JSON string containing recent price data (open, high, low, close, volume) in 'records' orientation,
                 or an error message if the fetch fails.
        """
        print(f"Executing tool fetch_realtime_price: symbol={symbol}")  # Debug
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(period="1d")
            if data.empty:
                return f"Error: No real-time data found for symbol {symbol}"
            data.reset_index(inplace=True)
            data["symbol"] = symbol
            data.rename(columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"}, inplace=True)
            return data[["symbol", "date", "open", "high", "low", "close", "volume"]].to_json(orient="records", date_format="iso")
        except Exception as e:
            return f"Error fetching real-time data for {symbol}: {str(e)}"
    
    
    # Tool: Analyze corporate action impact
    @mcp.tool()
    def corporate_action_impact(symbol: str, action_type: str) -> str:
        """
        Analyze the impact of a corporate action on stock price for a given symbol.
        Parameters:
            symbol (str): The stock symbol to analyze (e.g., 'AAPL').
            action_type (str): The type of corporate action (e.g., 'stock_split', 'dividend').
        Returns:
            str: JSON string with price changes before/after the action, or an error message.
        """
        print(f"Executing tool corporate_action_impact: symbol={symbol}, action_type={action_type}")  # Debug
        try:
            with engine.connect() as connection:
                with connection.begin():
                    query = "SELECT c.action_date, c.details, p.close FROM corporate_actions c JOIN prices p ON c.symbol = p.symbol AND c.action_date = p.date WHERE c.symbol = %s AND c.action_type = %s"
                    df = pd.read_sql(query, engine, params=(symbol, action_type))
                    if df.empty:
                        return f"Error: No {action_type} data found for {symbol}"
                    result = []
                    for _, row in df.iterrows():
                        action_date = row['action_date']
                        # Get price 5 days before and after
                        query_before = "SELECT close FROM prices WHERE symbol = %s AND date BETWEEN %s AND %s ORDER BY date DESC LIMIT 1"
                        query_after = "SELECT close FROM prices WHERE symbol = %s AND date BETWEEN %s AND %s ORDER BY date ASC LIMIT 1"
                        before_date = (pd.to_datetime(action_date) - timedelta(days=5)).strftime('%Y-%m-%d')
                        after_date = (pd.to_datetime(action_date) + timedelta(days=5)).strftime('%Y-%m-%d')
                        df_before = pd.read_sql(query_before, engine, params=(symbol, before_date, action_date))
                        df_after = pd.read_sql(query_after, engine, params=(symbol, action_date, after_date))
                        price_change = {
                            "action_date": str(action_date),
                            "details": json.loads(row['details']) if isinstance(row['details'], str) else row['details'],
                            "price_before": float(df_before['close'].iloc[0]) if not df_before.empty else None,
                            "price_at_action": float(row['close']),
                            "price_after": float(df_after['close'].iloc[0]) if not df_after.empty else None
                        }
                        result.append(price_change)
                    return json.dumps(result)
        except Exception as e:
            return f"Error analyzing {action_type} impact for {symbol}: {str(e)}"

    @mcp.tool()
    def financial_health(symbol: str, year: str) -> str:
        """
        Evaluate financial health of a stock for a given year using key ratios and metrics.
        Parameters:
            symbol (str): The stock symbol to analyze (e.g., 'META').
            year (str): The year to evaluate (e.g., '2024').
        Returns:
            str: JSON string with financial health metrics and a summary note, or an error message.
        """
        print(f"Executing tool financial_health: symbol={symbol}, year={year}")  # Debug
        try:
            with engine.connect() as connection:
                with connection.begin():
                    query = "SELECT date, current_ratio, debt_to_equity, roa, roe, net_income, revenue FROM financials WHERE symbol = %s AND YEAR(date) = %s"
                    df = pd.read_sql(query, engine, params=(symbol, year))
                    if df.empty:
                        return f"Error: No financial data found for {symbol} in {year}"
                    summary = {
                        "symbol": symbol,
                        "year": year,
                        "avg_current_ratio": float(df['current_ratio'].mean()),
                        "avg_debt_to_equity": float(df['debt_to_equity'].mean()),
                        "avg_roa": float(df['roa'].mean()),
                        "avg_roe": float(df['roe'].mean()),
                        "total_net_income": float(df['net_income'].sum()),
                        "total_revenue": float(df['revenue'].sum()),
                        "health_note": "Strong if current_ratio > 1, debt_to_equity < 1, positive ROA/ROE, and growing revenue"
                    }
                    return json.dumps(summary)
        except Exception as e:
            return f"Error evaluating financial health for {symbol} in {year}: {str(e)}"


    @mcp.tool()
    def get_company_overview(company_name: str) -> str:
        """
        Fetch a brief company overview from Wikipedia.

        Parameters:
            company_name (str): Name of the company (e.g., 'Apple Inc.', 'Google', 'Tesla').

        Returns:
            str: JSON string with the company name and summary, or an error message if the page is not found.
        """
        print(f"Fetching company overview from Wikipedia for: {company_name}")  # Debug
        try:
            user_agent = "CompanyInfoTool/1.0 (Contact: your_email@example.com)"
            wiki = wikipediaapi.Wikipedia(user_agent=user_agent, language='en')
            page = wiki.page(company_name)
            if not page.exists():
                return f"Error: Wikipedia page not found for '{company_name}'. Try a more precise name like 'Tesla Inc.'"

            info = {
                "name": page.title,
                "summary": page.summary
            }
            return json.dumps(info)
        except Exception as e:
            return f"Error fetching company overview: {str(e)}"

