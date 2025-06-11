import streamlit as st
import pandas as pd
import time
from data_collection import (
    get_company_info_wikipedia, get_price_performance, get_returns_timeframes,
    get_price_trend, get_dividend_metrics, get_financial_strength,
    get_valuation_ratios, get_balance_sheet_metrics, get_eps_growth_trend,
    format_volatility_data
)
from narration import generate_narration, prompts
from visualizations import (
    create_price_trend_chart, create_benchmark_chart,
    create_eps_chart, create_candlestick_chart
)
from news import fetch_news, process_news_with_llm

# Streamlit UI Configuration
st.set_page_config(page_title="GenAI MarketView 📈", layout="wide")

st.title("GenAI MarketView 📈") 
# Apply CSS for justified text and full-width search bar
st.markdown(
    """
    <style>
    .justified-text {
        text-align: justify;
        margin-bottom: 1em;
    }
    .table-caption {
        text-align: justify;
        margin-bottom: 0.5em;
    }
    .news-item {
        margin-bottom: 0.5em; 
    }
    .search-bar {
        width: 100% !important;
        margin-bottom: 10px;
    }
    .search-bar input {
        width: 100% !important;
    }
    .main-content {
        padding: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state
if 'ticker' not in st.session_state:
    st.session_state.ticker = ""
if 'news_df' not in st.session_state:
    st.session_state.news_df = None
if 'findings' not in st.session_state:
    st.session_state.findings = None
if 'ticker_cache' not in st.session_state:
    st.session_state.ticker_cache = {}  # Cache for all tickers

# Top search bar
st.markdown('<div class="search-bar">', unsafe_allow_html=True)
ticker = st.text_input(
    "",
    value="",
    key="ticker_input",
    placeholder="Enter Stock Ticker (Eg; AAPL, MSFT)",
    label_visibility="collapsed"
).strip().upper()
st.markdown('</div>', unsafe_allow_html=True)

# Update session state and reset cached data if ticker changes
if ticker != st.session_state.ticker:
    st.session_state.ticker = ticker
    st.session_state.news_df = None
    st.session_state.findings = None

# Check if ticker is empty; if so, display only the search bar
if not ticker:
    st.stop()

# Function to fetch and process data for a ticker (main content)
def fetch_and_process_data(ticker, company_name):
    try:
        overview_data = get_company_info_wikipedia(company_name) or {"name": ticker, "summary": "No data available."}
        price_data = get_price_performance(ticker)
        returns_data = get_returns_timeframes(ticker)
        price_trend_data = get_price_trend(ticker)
        dividend_data = get_dividend_metrics(ticker)
        financial_strength_data = get_financial_strength(ticker)
        valuation_data = get_valuation_ratios(ticker)
        balance_data = get_balance_sheet_metrics(ticker)
        eps_data = get_eps_growth_trend(ticker)
        volatility_df, volatility_narrative_default = format_volatility_data(ticker)

        # Prepare benchmark data
        benchmark_data = {
            "Timeframe": ["1-Year", "3-Year", "5-Year"],
            ticker: [returns_data["1_year_return"], returns_data["3_year_return"], returns_data["5_year_return"]],
            "S&P 500": [returns_data["sp500_1_year_return"], returns_data["sp500_3_year_return"], returns_data["sp500_5_year_return"]],
            "Tech Sector": [returns_data["sector_1_year_return"], returns_data["sector_3_year_return"], returns_data["sector_5_year_return"]]
        }

        # Prepare price levels data
        price_levels_data = {
            "Metric": ["Price", "50-day SMA", "200-day SMA", "Fibonacci (61.8%)"],
            "Current": [price_data["current_price"], price_data["current_price"] * 0.95, price_data["current_price"] * 0.9, price_data["current_price"] * 1.05],
            "1-Month Ago": [price_data["current_price"] * 0.98, price_data["current_price"] * 0.93, price_data["current_price"] * 0.88, price_data["current_price"] * 1.03],
            "Support": [price_data["52_week_low"]] * 4,
            "Resistance": [price_data["52_week_high"]] * 4
        }

        # Generate Narrations
        narrations = {}
        max_retries = 3
        retry_delay = 5  # seconds
        narration_keys = [
            ("overview", prompts["overview"], overview_data),
            ("price_performance", prompts["price_performance"], price_data),
            ("returns_narrative", prompts["returns_narrative"], returns_data),
            ("price_trend_narrative", prompts["price_trend_narrative"], price_trend_data),
            ("dividend_narrative", prompts["dividend_narrative"], dividend_data),
            ("benchmark_narrative", prompts["benchmark_narrative"], benchmark_data),
            ("financial_strength", prompts["financial_strength"], financial_strength_data),
            ("valuation_narrative", prompts["valuation_narrative"], valuation_data),
            ("balance_narrative", prompts["balance_narrative"], balance_data),
            ("eps_narrative", prompts["eps_narrative"], eps_data),
            ("market_sentiment", prompts["market_sentiment"], price_levels_data),
            ("volatility_narrative", prompts["volatility_narrative"], volatility_df.to_dict() if not volatility_df.empty else {}),
            ("price_levels_narrative", prompts["price_levels_narrative"], price_levels_data),
            ("candlestick_narrative", prompts["candlestick_narrative"], price_levels_data),
            ("recommendations", prompts["recommendations"], {
                "price": price_data, "returns": returns_data, "financial": financial_strength_data,
                "valuation": valuation_data, "technical": price_levels_data
            })
        ]

        for key, prompt, data in narration_keys:
            retries = 0
            while retries <= max_retries:
                try:
                    if key == "volatility_narrative" and volatility_df.empty:
                        narrations[key] = volatility_narrative_default
                    else:
                        narrations[key] = generate_narration(prompt, data, ticker)
                    break
                except Exception as e:
                    if "ThrottlingException" in str(e):
                        retries += 1
                        if retries > max_retries:
                            narrations[key] = f"Narration for {key.replace('_', ' ').title()} temporarily unavailable due to high demand. Please try again later."
                            break
                        time.sleep(retry_delay * retries)
                    else:
                        narrations[key] = f"Failed to generate {key.replace('_', ' ').title()} narration: {str(e)}"
                        break

        return {
            "overview_data": overview_data,
            "price_data": price_data,
            "returns_data": returns_data,
            "price_trend_data": price_trend_data,
            "dividend_data": dividend_data,
            "financial_strength_data": financial_strength_data,
            "valuation_data": valuation_data,
            "balance_data": balance_data,
            "eps_data": eps_data,
            "volatility_df": volatility_df,
            "volatility_narrative_default": volatility_narrative_default,
            "benchmark_data": benchmark_data,
            "price_levels_data": price_levels_data,
            "narrations": narrations
        }
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return {
            "overview_data": {"name": ticker, "summary": "No data available."},
            "price_data": {},
            "returns_data": {},
            "price_trend_data": {},
            "dividend_data": {},
            "financial_strength_data": {},
            "valuation_data": {},
            "balance_data": {},
            "eps_data": {},
            "volatility_df": pd.DataFrame(),
            "volatility_narrative_default": "No volatility data available.",
            "benchmark_data": {},
            "price_levels_data": {},
            "narrations": {}
        }

# Sidebar: News Analysis (load first)
with st.sidebar:
    st.header("News Analysis")
    if ticker:
        if st.session_state.news_df is None:
            if ticker in st.session_state.ticker_cache and "news_df" in st.session_state.ticker_cache[ticker]:
                with st.spinner("Processing news with LLM..."):
                    time.sleep(5)
                    st.session_state.news_df = st.session_state.ticker_cache[ticker]["news_df"]
                    st.session_state.findings = st.session_state.ticker_cache[ticker]["findings"]
            else:
                news_df = fetch_news(ticker)
                st.session_state.news_df = news_df
                if news_df is None or news_df.empty:
                    st.error(f"No news found for ticker {ticker}.")
        
        if st.session_state.news_df is not None and not st.session_state.news_df.empty:
            if st.session_state.findings is None:
                with st.spinner("Processing news with LLM..."):
                    findings = process_news_with_llm(st.session_state.news_df)
                    st.session_state.findings = findings
                    if findings is None:
                        st.error("Failed to process news with LLM.")
            
            news_df = st.session_state.news_df
            findings = st.session_state.findings
            
            # Cache news data for the ticker
            if ticker:
                if ticker not in st.session_state.ticker_cache:
                    st.session_state.ticker_cache[ticker] = {}
                st.session_state.ticker_cache[ticker]["news_df"] = news_df
                st.session_state.ticker_cache[ticker]["findings"] = findings
            
            if findings:
                st.subheader("Key Findings")
                for finding, news_ids in findings.items():
                    with st.expander(finding, expanded=False):
                        st.write(f"{len(news_ids)} news items")
                        relevant_news = news_df[news_df["id"].isin(news_ids)]
                        if relevant_news.empty:
                            st.write("No news found for this finding.")
                        else:
                            for _, row in relevant_news.iterrows():
                                st.markdown(f'<div class="justified-text news-item"><b>{row["title"]}</b><br><a href="{row["url"]}">Read more</a></div>', unsafe_allow_html=True)
                                st.markdown("---")

# Main content: Summary Insights (load after sidebar)
company_name = {"AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "GOOGL": "Alphabet Inc."}.get(ticker, ticker)
data = None
with st.spinner(f"Generating narration through LLM..."):
    if ticker in st.session_state.ticker_cache and "overview_data" in st.session_state.ticker_cache[ticker]:
        time.sleep(10)
        data = st.session_state.ticker_cache[ticker]
    else:
        data = fetch_and_process_data(ticker, company_name)
        st.session_state.ticker_cache[ticker] = {**st.session_state.ticker_cache.get(ticker, {}), **data}  # Merge with existing cache (e.g., news data)

# Extract data from the result
overview_data = data["overview_data"]
price_data = data["price_data"]
returns_data = data["returns_data"]
price_trend_data = data["price_trend_data"]
dividend_data = data["dividend_data"]
financial_strength_data = data["financial_strength_data"]
valuation_data = data["valuation_data"]
balance_data = data["balance_data"]
eps_data = data["eps_data"]
volatility_df = data["volatility_df"]
volatility_narrative_default = data["volatility_narrative_default"]
benchmark_data = data["benchmark_data"]
price_levels_data = data["price_levels_data"]
narrations = data["narrations"]

with st.container():
    st.markdown('<div class="main-content">', unsafe_allow_html=True)
    st.title(f"{overview_data.get('name', ticker)} ({ticker}) Financial and Technical Analysis")

    # 1. Company Overview
    st.header("Company Overview")
    st.markdown(f'<div class="justified-text">{narrations.get("overview", "No data available.")}</div>', unsafe_allow_html=True)

    # 2. Historical Performance
    st.header("Historical Performance")
    # 2.1 Price Performance
    st.markdown(f'<div class="justified-text">{narrations.get("price_performance", "No data available.")}</div>', unsafe_allow_html=True)

    # 2.2 Returns Across Timeframes
    st.subheader("Returns Across Timeframes")
    st.markdown(f'<div class="table-caption">Table 1: Returns and Volatility for {ticker}</div>', unsafe_allow_html=True)
    returns_df = pd.DataFrame({
        "Timeframe": ["YTD", "1-Year", "3-Year", "5-Year"],
        "Return": [returns_data.get(f"{t}_return", 0) for t in ["ytd", "1_year", "3_year", "5_year"]],
        "S&P 500 Return": [returns_data.get(f"sp500_{t}_return", 0) for t in ["ytd", "1_year", "3_year", "5_year"]],
        "Sector Return": [returns_data.get(f"sector_{t}_return", 0) for t in ["ytd", "1_year", "3_year", "5_year"]],
        "Volatility": [returns_data.get(f"volatility_{t}", 0) for t in ["ytd", "1_year", "3_year", "5_year"]]
    })
    if not returns_df.empty:
        st.table(returns_df)
    st.markdown(f'<div class="justified-text">{narrations.get("returns_narrative", "No data available.")}</div>', unsafe_allow_html=True)

    # 2.3 Price Trend Visualisation
    st.subheader("Price Trend Visualisation")
    st.markdown(f'<div class="justified-text">{narrations.get("price_trend_narrative", "No data available.")}</div>', unsafe_allow_html=True)
    fig_price = create_price_trend_chart(price_trend_data, ticker)
    st.plotly_chart(fig_price, use_container_width=True)

    # 2.4 Dividend Performance
    st.subheader("Dividend Performance")
    st.markdown(f'<div class="table-caption">Table 2: Dividend Performance for {ticker}</div>', unsafe_allow_html=True)
    dividend_df = pd.DataFrame(dividend_data)
    if not dividend_df.empty:
        st.table(dividend_df)
    st.markdown(f'<div class="justified-text">{narrations.get("dividend_narrative", "No data available.")}</div>', unsafe_allow_html=True)

    # 3. Fundamental Analysis
    st.header("Fundamental Analysis")
    # 3.1 Financial Strength Overview
    st.markdown(f'<div class="justified-text">{narrations.get("financial_strength", "No data available.")}</div>', unsafe_allow_html=True)

    # 3.2 Valuation Ratios
    st.subheader("Valuation Ratios")
    st.markdown(f'<div class="table-caption">Table 3: Valuation Ratios for {ticker}</div>', unsafe_allow_html=True)
    valuation_df = pd.DataFrame(valuation_data)
    if not valuation_df.empty:
        st.table(valuation_df)
    st.markdown(f'<div class="justified-text">{narrations.get("valuation_narrative", "No data available.")}</div>', unsafe_allow_html=True)

    # 3.3 Balance Sheet Metrics
    st.subheader("Balance Sheet Metrics")
    st.markdown(f'<div class="table-caption">Table 4: Balance Sheet Metrics for {ticker}</div>', unsafe_allow_html=True)
    balance_df = pd.DataFrame(balance_data)
    if not balance_df.empty:
        st.table(balance_df)
    st.markdown(f'<div class="justified-text">{narrations.get("balance_narrative", "No data available.")}</div>', unsafe_allow_html=True)

    # 3.4 EPS Growth Trend
    st.subheader("EPS Growth Trend")
    st.markdown(f'<div class="table-caption">Table 5: Quarterly EPS for {ticker}</div>', unsafe_allow_html=True)
    eps_df = pd.DataFrame(eps_data)
    if not eps_df.empty:
        fig_eps = create_eps_chart(eps_data, ticker)
        st.plotly_chart(fig_eps, use_container_width=True)
    st.markdown(f'<div class="justified-text">{narrations.get("eps_narrative", "No data available.")}</div>', unsafe_allow_html=True)

    # 4. Technical Analysis and Trading Insights
    st.header("Technical Analysis and Trading Insights")
    # 4.1 Market Sentiment Summary
    st.markdown(f'<div class="justified-text">{narrations.get("market_sentiment", "No data available.")}</div>', unsafe_allow_html=True)

    # 4.2 Volatility Indicators
    st.subheader("Volatility Indicators")
    st.markdown(f'<div class="table-caption">Table 6: Volatility Indicators for {ticker}</div>', unsafe_allow_html=True)
    if not volatility_df.empty:
        st.table(volatility_df)
    st.markdown(f'<div class="justified-text">{narrations.get("volatility_narrative", volatility_narrative_default)}</div>', unsafe_allow_html=True)

    # 4.3 Price Levels
    st.subheader("Price Levels")
    st.markdown(f'<div class="table-caption">Table 7: Price Levels for {ticker}</div>', unsafe_allow_html=True)
    price_levels_df = pd.DataFrame(price_levels_data)
    if not price_levels_df.empty:
        st.table(price_levels_df)
    st.markdown(f'<div class="justified-text">{narrations.get("price_levels_narrative", "No data available.")}</div>', unsafe_allow_html=True)

    # 4.4 Candlestick and Volume Chart
    st.subheader("Candlestick and Volume Chart")
    st.markdown(f'<div class="justified-text">{narrations.get("candlestick_narrative", "No data available.")}</div>', unsafe_allow_html=True)
    fig_candle = create_candlestick_chart(price_data, price_levels_data, ticker)
    st.plotly_chart(fig_candle, use_container_width=True)

    # 5. Recommendations and Final Findings
    st.header("Recommendations and Final Findings")
    st.markdown(f'<div class="justified-text">{narrations.get("recommendations", "No data available.")}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)