import pandas as pd
import yfinance as yf
import wikipediaapi
import numpy as np
from datetime import datetime, timedelta
import pytz

def get_company_info_wikipedia(company_name):
    user_agent = "StockAnalysisBot/1.0 (Contact: example@example.com)"
    wiki = wikipediaapi.Wikipedia(user_agent=user_agent, language='en')
    page = wiki.page(company_name)
    if not page.exists():
        return None
    return {
        "name": page.title,
        "summary": page.summary[:500] + "..." if len(page.summary) > 500 else page.summary
    }

def get_price_performance(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    history = stock.history(period="5y")
    today = datetime.now()
    current_price = info.get("currentPrice", 0)
    market_cap = info.get("marketCap", 0)
    ytd_start = history[history.index >= f"{today.year}-01-01"].iloc[0]["Close"] if not history[history.index >= f"{today.year}-01-01"].empty else 0
    ytd_return = ((current_price - ytd_start) / ytd_start) * 100 if ytd_start else 0
    return {
        "current_price": current_price,
        "ytd_return": round(ytd_return, 2),
        "market_cap": market_cap,
        "52_week_high": info.get("fiftyTwoWeekHigh", 0),
        "52_week_low": info.get("fiftyTwoWeekLow", 0)
    }

def get_returns_timeframes(ticker):
    stock = yf.Ticker(ticker)
    history = stock.history(period="5y")
    sp500 = yf.Ticker("^GSPC").history(period="5y")
    info = stock.info
    sector_name = info.get("sector", "Technology")
    sector_etf_map = {
        "Technology": "XLK", "Healthcare": "XLV", "Financial Services": "XLF",
        "Industrials": "XLI", "Energy": "XLE", "Utilities": "XLU",
        "Consumer Cyclical": "XLY", "Consumer Defensive": "XLP",
        "Basic Materials": "XLB", "Real Estate": "XLRE", "Communication Services": "XLC"
    }
    sector_etf = sector_etf_map.get(sector_name)
    sector_data = yf.Ticker(sector_etf).history(period="5y") if sector_etf else None
    today = datetime.now()

    def calc_return(data, period):
        return round(((data.iloc[-1]["Close"] - data.iloc[-period]["Close"]) / data.iloc[-period]["Close"] * 100), 2) if len(data) >= period else 0

    def calc_ytd_return(data):
        ytd_data = data[data.index >= f"{today.year}-01-01"]
        return round(((data.iloc[-1]["Close"] - ytd_data.iloc[0]["Close"]) / ytd_data.iloc[0]["Close"] * 100), 2) if len(ytd_data) > 0 else 0

    def calc_volatility(data, period=None):
        if period:
            data = data.iloc[-period:]
        return round(data["Close"].pct_change().std() * (252 ** 0.5) * 100, 2) if not data.empty else 0

    return {
        "ytd_return": calc_ytd_return(history),
        "1_year_return": calc_return(history, 252),
        "3_year_return": calc_return(history, 756),
        "5_year_return": calc_return(history, len(history)),
        "sp500_ytd_return": calc_ytd_return(sp500),
        "sp500_1_year_return": calc_return(sp500, 252),
        "sp500_3_year_return": calc_return(sp500, 756),
        "sp500_5_year_return": calc_return(sp500, len(sp500)),
        "sector_ytd_return": calc_ytd_return(sector_data) if sector_data is not None else 0,
        "sector_1_year_return": calc_return(sector_data, 252) if sector_data is not None else 0,
        "sector_3_year_return": calc_return(sector_data, 756) if sector_data is not None else 0,
        "sector_5_year_return": calc_return(sector_data, len(sector_data)) if sector_data is not None else 0,
        "volatility_ytd": calc_volatility(history[history.index >= f"{today.year}-01-01"]),
        "volatility_1_year": calc_volatility(history, 252),
        "volatility_3_year": calc_volatility(history, 756),
        "volatility_5_year": calc_volatility(history)
    }

def get_price_trend(ticker):
    stock = yf.Ticker(ticker)
    history = stock.history(period="5y")
    closing_prices = {str(date): price for date, price in history["Close"].to_dict().items()}
    return {"5_year_closing_prices": closing_prices}

def get_dividend_metrics(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    dividends = stock.dividends
    history = stock.history(period="5y")
    earnings = stock.income_stmt
    current_price = history['Close'].iloc[-1] if not history.empty else 0
    current_dividend = info.get('dividendRate', 0)
    dividend_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
    dividend_payout = current_dividend
    eps = info.get('trailingEps', 0)
    payout_ratio = (current_dividend / eps) * 100 if eps else 0
    one_year_ago = datetime.now(pytz.UTC) - timedelta(days=365)
    past_dividends = dividends[dividends.index >= one_year_ago - timedelta(days=30)]
    dividend_yield_1yr = info.get('trailingAnnualDividendYield', 0) * 100 if info.get('trailingAnnualDividendYield') else 0
    dividend_1yr = info.get('trailingAnnualDividendRate', 0)
    payout_ratio_1yr = (dividend_1yr / eps) * 100 if eps else 0
    five_years_ago = datetime.now(pytz.UTC) - timedelta(days=5*365)
    five_year_dividends = dividends[dividends.index >= five_years_ago]
    dividend_5yr_avg_yield = info.get('fiveYearAvgDividendYield', 0)
    dividend_5yr_avg = five_year_dividends.mean() * 4 if not five_year_dividends.empty else 0
    dividend_growth = ((current_dividend - dividend_1yr) / dividend_1yr * 100) if dividend_1yr else 0
    return {
        "Metric": ["Dividend Yield", "Dividend Payout", "Payout Ratio", "Dividend Growth"],
        "Current": [f"{dividend_yield:.2f}%", f"{dividend_payout:.2f}", f"{payout_ratio:.2f}%", f"{dividend_growth:.2f}%"],
        "1-Yr Ago": [f"{dividend_yield_1yr:.2f}%", f"{dividend_1yr:.2f}", f"{payout_ratio_1yr:.2f}%", "-"],
        "5-Yr Avg": [f"{dividend_5yr_avg_yield:.2f}%", f"{dividend_5yr_avg:.2f}", "-", "-"],
        "Industry Avg": ["1.2%", "1.50", "20.0%", "5.0%"]
    }

def calculate_dcf(ticker, years=5, discount_rate=0.10, growth_rate=0.05):
    stock = yf.Ticker(ticker)
    cash_flows = stock.cashflow
    fcf = cash_flows.loc['Free Cash Flow'].iloc[0] if 'Free Cash Flow' in cash_flows.index else 0
    future_cash_flows = [fcf * (1 + growth_rate) ** year for year in range(1, years + 1)]
    present_values = [cf / (1 + discount_rate) ** year for year, cf in enumerate(future_cash_flows, 1)]
    terminal_value = future_cash_flows[-1] * (1 + growth_rate) / (discount_rate - growth_rate)
    pv_terminal = terminal_value / (1 + discount_rate) ** years
    total_pv = sum(present_values) + pv_terminal
    shares = stock.info.get('sharesOutstanding', 1)
    return total_pv / shares if shares else 0

def get_financial_strength(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    balance_sheet = stock.balance_sheet
    profit_margin = info.get("profitMargins", 0) * 100
    cash_reserves = balance_sheet.loc['Cash'].iloc[0] if 'Cash' in balance_sheet.index else info.get('totalCash', 0)
    return {
        "profit_margin": profit_margin,
        "cash_reserves": cash_reserves,
        "pe_ratio": info.get("forwardPE", 0),
        "dcf_intrinsic_value": round(calculate_dcf(ticker), 2)
    }

def get_valuation_ratios(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    market_cap = info.get("marketCap", 0)
    return {
        "Metric": ["P/E Ratio", "P/B Ratio", "PEG Ratio", "EV/EBITDA", "FCF Yield"],
        ticker: [
            info.get("forwardPE", None),
            info.get("priceToBook", None),
            info.get("pegRatio", None),
            info.get("enterpriseToEbitda", None),
            (info.get("freeCashflow", 0) / market_cap * 100) if market_cap else None
        ],
        "Industry Avg": [28.0, 7.0, 2.0, 18.0, 4.0],
        "Peer Avg": [30.0, 8.0, 2.2, 20.0, 4.0]
    }

def get_balance_sheet_metrics(ticker):
    stock = yf.Ticker(ticker)
    balance_sheet = stock.balance_sheet
    financials = stock.financials
    metrics = {
        "Metric": ["Cash ($B)", "Current Ratio", "Equity ($B)", "Net Income ($B)", "Revenue ($B)", "ROE (%)", "Total Debt ($B)"],
        "TTM": [None] * 7,
        "1-Yr Ago": [None] * 7,
        "Industry Avg": [50, 1.5, 60, 50.0, 200.0, 120, 80]
    }
    if not balance_sheet.empty and not financials.empty:
        latest_balance = balance_sheet.iloc[:, 0]
        latest_financials = financials.iloc[:, 0]
        metrics["TTM"][0] = latest_balance.get("Cash", 0) / 1e9
        metrics["TTM"][1] = latest_balance.get("Total Current Assets", 0) / latest_balance.get("Total Current Liabilities", 1)
        metrics["TTM"][2] = latest_balance.get("Total Stockholder Equity", 0) / 1e9
        metrics["TTM"][3] = latest_financials.get("Net Income", 0) / 1e9
        metrics["TTM"][4] = latest_financials.get("Total Revenue", 0) / 1e9
        metrics["TTM"][5] = (latest_financials.get("Net Income", 0) / latest_balance.get("Total Stockholder Equity", 1)) * 100
        metrics["TTM"][6] = latest_balance.get("Total Liabilities", 0) / 1e9
    return metrics

def get_eps_growth_trend(ticker):
    stock = yf.Ticker(ticker)
    quarterly_financials = stock.quarterly_financials
    info = stock.info
    tz = pytz.timezone('America/New_York')
    eps_quarterly = []
    if not quarterly_financials.empty:
        shares = info.get('sharesOutstanding', None)
        for i in range(min(20, quarterly_financials.shape[1])):
            quarter_data = quarterly_financials.iloc[:, i]
            net_income = quarter_data.get('Net Income', None)
            date = pd.Timestamp(quarter_data.name).tz_localize(tz).strftime('%Y-%m-%d') if quarter_data.name else None
            eps = net_income / shares if net_income and shares else None
            if date:
                eps_quarterly.append({"date": date, "eps": eps})
    return sorted(eps_quarterly, key=lambda x: x["date"]) if eps_quarterly else []

def get_volatility_indicators(ticker):
    stock = yf.Ticker(ticker)
    vix_ticker = "^VIX"
    sp500_ticker = "^GSPC"
    vix = yf.Ticker(vix_ticker)
    sp500 = yf.Ticker(sp500_ticker)
    tz = pytz.timezone('America/New_York')

    end_date = datetime.now(tz)
    start_date = end_date - timedelta(days=365)
    start_date_5y = end_date - timedelta(days=5*365)

    hist_data = stock.history(start=start_date, end=end_date, interval="1d")
    vix_data = vix.history(start=start_date, end=end_date, interval="1d")
    aapl_5y = stock.history(start=start_date_5y, end=end_date, interval="1d")
    sp500_5y = sp500.history(start=start_date_5y, end=end_date, interval="1d")

    volatility_indicators = []

    def calculate_atr(data, periods=14):
        if data.empty:
            return None
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=periods).mean().iloc[-1]
        return atr if pd.notna(atr) else None

    atr_current = calculate_atr(hist_data)
    atr_1m_ago = calculate_atr(hist_data[:-21])
    atr_signal = "High" if atr_current and atr_current > 3.0 else "Moderate" if atr_current else None
    atr_trend = "Up" if atr_current and atr_1m_ago and atr_current > atr_1m_ago else "Down" if atr_current and atr_1m_ago else None

    def calculate_bollinger_width(data, periods=20):
        if data.empty:
            return None
        sma = data['Close'].rolling(window=periods).mean()
        std = data['Close'].rolling(window=periods).std()
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        bollinger_width = ((upper_band - lower_band) / sma * 100).iloc[-1]
        return bollinger_width if pd.notna(bollinger_width) else None

    bollinger_width_current = calculate_bollinger_width(hist_data)
    bollinger_width_1m_ago = calculate_bollinger_width(hist_data[:-21])
    bollinger_signal = "Expanding" if bollinger_width_current and bollinger_width_current > 12 else "Neutral" if bollinger_width_current else None
    bollinger_trend = "Up" if bollinger_width_current and bollinger_width_1m_ago and bollinger_width_current > bollinger_width_1m_ago else "Down" if bollinger_width_current and bollinger_width_1m_ago else None

    def calculate_vix_correlation(stock_data, vix_data):
        if stock_data.empty or vix_data.empty:
            return None
        aligned_data = pd.concat([stock_data['Close'].pct_change(), vix_data['Close'].pct_change()], axis=1).dropna()
        correlation = aligned_data.corr().iloc[0, 1]
        return correlation if pd.notna(correlation) else None

    vix_correlation_current = calculate_vix_correlation(hist_data, vix_data)
    vix_correlation_1m_ago = calculate_vix_correlation(hist_data[:-21], vix_data[:-21])
    vix_corr_signal = ("Moderate" if vix_correlation_current and 0.4 <= abs(vix_correlation_current) <= 0.7 else
                      "High" if vix_correlation_current and abs(vix_correlation_current) > 0.7 else
                      "Low" if vix_correlation_current else None)
    vix_corr_trend = "Up" if vix_correlation_current and vix_correlation_1m_ago and abs(vix_correlation_current) > abs(vix_correlation_1m_ago) else "Stable" if vix_correlation_current and vix_correlation_1m_ago else None

    def calculate_beta(stock_data, market_data):
        if stock_data.empty or market_data.empty:
            return None
        returns = pd.concat([stock_data['Close'].pct_change(), market_data['Close'].pct_change()], axis=1).dropna()
        cov_matrix = returns.cov()
        beta = cov_matrix.iloc[0, 1] / returns.iloc[:, 1].var()
        return beta if pd.notna(beta) else None

    beta_current = calculate_beta(aapl_5y, sp500_5y)
    beta_1m_ago = calculate_beta(aapl_5y[:-21], sp500_5y[:-21])
    beta_signal = "High" if beta_current and beta_current > 1.0 else "Low" if beta_current else None
    beta_trend = "Up" if beta_current and beta_1m_ago and beta_current > beta_1m_ago else "Down" if beta_current and beta_1m_ago else None

    volatility_indicators.extend([
        {
            'indicator': 'ATR (14-day)',
            'value': atr_current,
            'signal': atr_signal,
            '1_month_ago': atr_1m_ago,
            'trend': atr_trend
        },
        {
            'indicator': 'Bollinger Width',
            'value': bollinger_width_current,
            'signal': bollinger_signal,
            '1_month_ago': bollinger_width_1m_ago,
            'trend': bollinger_trend
        },
        {
            'indicator': 'VIX Correlation',
            'value': vix_correlation_current,
            'signal': vix_corr_signal,
            '1_month_ago': vix_correlation_1m_ago,
            'trend': vix_corr_trend
        },
        {
            'indicator': '5-Year Beta',
            'value': beta_current,
            'signal': beta_signal,
            '1_month_ago': beta_1m_ago,
            'trend': beta_trend
        }
    ])

    return volatility_indicators

def format_volatility_data(ticker):
    volatility_data = get_volatility_indicators(ticker)

    if not volatility_data:
        return pd.DataFrame(), "No volatility data available for the specified ticker."

    df = pd.DataFrame(volatility_data)
    if not df.empty:
        df['value'] = df.apply(lambda row: f"{row['value']:.2f}" if row['indicator'] == 'ATR (14-day)' and pd.notna(row['value'])
                                  else f"{row['value']:.2f}%" if row['indicator'] == 'Bollinger Width' and pd.notna(row['value'])
                                  else f"{row['value']:.2f}" if pd.notna(row['value']) else None, axis=1)
        df['1_month_ago'] = df.apply(lambda row: f"{row['1_month_ago']:.2f}" if row['indicator'] == 'ATR (14-day)' and pd.notna(row['1_month_ago'])
                                    else f"{row['1_month_ago']:.2f}%" if row['indicator'] == 'Bollinger Width' and pd.notna(row['1_month_ago'])
                                    else f"{row['1_month_ago']:.2f}" if pd.notna(row['1_month_ago']) else None, axis=1)
        df = df[['indicator', 'value', 'signal', '1_month_ago', 'trend']]
        df.columns = ['Indicator', 'Value', 'Signal', '1-Month Ago', 'Trend']

    narrative = f"Volatility indicators for {ticker}, including ATR (14-day), Bollinger Width, VIX Correlation, and 5-Year Beta, based on Yahoo Finance data."
    return df, narrative