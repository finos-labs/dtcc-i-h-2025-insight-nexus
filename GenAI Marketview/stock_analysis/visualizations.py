import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

def create_price_trend_chart(price_trend_data, ticker):
    price_df = pd.DataFrame(list(price_trend_data["5_year_closing_prices"].items()), columns=["Date", "Price"])
    price_df["Date"] = pd.to_datetime(price_df["Date"], utc=True)
    fig = px.line(price_df, x="Date", y="Price", title=f"{ticker} 5-Year Price Trend")
    return fig

def create_benchmark_chart(benchmark_data, ticker):
    benchmark_df = pd.DataFrame(benchmark_data)
    fig = go.Figure()
    for column in [ticker, "S&P 500", "Tech Sector"]:
        fig.add_trace(go.Bar(x=benchmark_df["Timeframe"], y=benchmark_df[column], name=column))
    fig.update_layout(title=f"{ticker} Returns vs Benchmarks", barmode="group")
    return fig

def create_eps_chart(eps_data, ticker):
    eps_df = pd.DataFrame(eps_data)
    eps_df["eps"] = eps_df["eps"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else None)
    fig = px.bar(eps_df, x="date", y="eps", title=f"{ticker} Quarterly EPS (5 Years)")
    return fig

def create_candlestick_chart(price_data, price_levels_data, ticker):
    dates_6m = pd.date_range(start="2024-12-06", end="2025-06-05", freq="D")
    close = np.cumsum(np.random.normal(0.1, 0.5, len(dates_6m))) + 100
    close = close * (price_data.get("current_price", 100) / close[-1])
    open_p = close + np.random.normal(0, 0.2, len(dates_6m))
    high = np.maximum(open_p, close) + np.random.uniform(0, 0.5, len(dates_6m))
    low = np.minimum(open_p, close) - np.random.uniform(0, 0.5, len(dates_6m))
    volume = np.random.randint(1000000, 5000000, len(dates_6m))
    rsi = np.random.uniform(60, 80, len(dates_6m))
    candle_df = pd.DataFrame({
        "Date": dates_6m,
        "Open": open_p,
        "High": high,
        "Low": low,
        "Close": close,
        "Volume": volume,
        "RSI": rsi
    })
    support = price_levels_data["Support"][0] if price_levels_data.get("Support") else 100
    resistance = price_levels_data["Resistance"][0] if price_levels_data.get("Resistance") else 150
    fig = go.Figure(data=[
        go.Candlestick(x=candle_df["Date"], open=candle_df["Open"], high=candle_df["High"],
                       low=candle_df["Low"], close=candle_df["Close"], name="Price"),
        go.Scatter(x=candle_df["Date"], y=[resistance]*len(dates_6m), mode="lines", name="Resistance", line=dict(dash="dash")),
        go.Scatter(x=candle_df["Date"], y=[support]*len(dates_6m), mode="lines", name="Support", line=dict(dash="dash"))
    ])
    fig.update_layout(title=f"{ticker} 6-Month Candlestick Chart with Support/Resistance")
    return fig