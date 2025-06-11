import boto3
import json
import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# AWS Bedrock client setup
try:
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )
except Exception as e:
    st.error(f"Failed to initialize Bedrock client: {e}")
    bedrock_runtime = None

MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

# Narration Generation
def generate_narration(prompt, data, ticker):
    if not bedrock_runtime:
        return f"No narration available for {ticker}."
    messages = [{"role": "user", "content": [{"text": prompt.format(ticker=ticker, data=json.dumps(data))}]}]
    try:
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=[{"text": f"You are a financial analyst for {ticker}. Generate concise, professional narrations in plain text with no formatting or emphasis. Do not include section headings. Follow the provided format and use the data provided."}],
            inferenceConfig={"maxTokens": 500, "temperature": 0.7}
        )
        return response["output"]["message"]["content"][0]["text"]
    except Exception as e:
        st.warning(f"Failed to generate narration: {e}")
        return f"No narration available for {ticker}."

# Prompts for Each Section
prompts = {
    "overview": """
Generate a company overview narration for {ticker} in plain text. Summarize the company's history, key products/services, and major milestones based on the data: {data}. Keep it concise (100-150 words).
Example:
Apple Inc. (AAPL), founded in 1976 by Steve Jobs, Steve Wozniak, and Ronald Wayne, is a global leader in consumer electronics, software, and services. Headquartered in Cupertino, California, Apple is renowned for its iPhone, iPad, Mac, and Apple Watch, alongside services like Apple Music and iCloud. Key milestones include the iPhone launch in 2007 and reaching a 3 trillion market cap in 2023.
""",
    "price_performance": """
Generate a price performance narration for {ticker} in plain text. Highlight YTD return, market cap, 52-week high/low, and key drivers using the data: {data}. Keep it concise (50-75 words).
Example:
{ticker} has a year-to-date return of 18%, with a market cap of 2.8 trillion. The stock hit a 52-week high of 137, driven by iPhone 16 sales and Apple Intelligence integrations. Recent earnings exceeded expectations, though tariff risks loom.
""",
    "returns_narrative": """
Generate a returns narration for {ticker} in plain text. Summarize returns and volatility across timeframes compared to S&P 500 and sector using the data: {data}. Keep it concise (50-75 words).
Example:
{ticker}'s outperformance shows returns of 18% YTD, 25% over 1 year, 120% over 3 years, and 298% over 5 years compared to the S&P 500 and sector. Volatility (20-25%) suggests favorable risk-adjusted returns.
""",
    "price_trend_narrative": """
Generate a price trend narration for {ticker} in plain text. Describe the 5-year price trend and key events using the data: {data}. Keep it concise (50-75 words).
Example:
{ticker}'s 5-year price trend shows steady growth with spikes during iPhone launches (e.g., 2022). A dip in 2022 reflected supply chain issues, while the 2023 Vision Pro launch drove gains.
""",
    "dividend_narrative": """
Generate a dividend performance narration for {ticker} in plain text. Discuss dividend yield, payout, and strategy compared to industry using the data: {data}. Keep it concise (50-75 words).
Example:
{ticker}'s conservative dividend strategy yields 0.8%, below the industry average of 1.2%, with a payout of 1.00 and a low payout ratio of 12.8%, indicating earnings retention.
""",
    "benchmark_narrative": """
Generate a benchmark comparison narration for {ticker} in plain text. Compare returns to S&P 500 and sector using the data: {data}. Keep it concise (30-50 words).
Example:
{ticker}'s returns outperform the S&P 500 and tech sector over 1, 3, and 5 years, emphasizing its consistent market leadership.
""",
    "financial_strength": """
Generate a financial strength narration for {ticker} in plain text. Highlight profit margin, cash reserves, P/E, and DCF valuation using the data: {data}. Keep it concise (50-75 words).
Example:
{ticker}'s 31% profit margin and 250 billion in cash reserves highlight its strength. A P/E ratio of 36.2 suggests a premium valuation, with DCF estimates indicating an intrinsic value of 110-130.
""",
    "valuation_narrative": """
Generate a valuation ratios narration for {ticker} in plain text. Discuss key ratios compared to industry and peers using the data: {data}. Keep it concise (50-75 words).
Example:
{ticker}'s premium valuation shows a P/E ratio of 36.2 and P/B ratio of 40.1, significantly above industry and peer averages, reflecting high market expectations.
""",
    "balance_narrative": """
Generate a balance sheet narration for {ticker} in plain text. Highlight key metrics like cash, revenue, and ROE compared to industry using the data: {data}. Keep it concise (50-75 words).
Example:
{ticker}'s robust position includes 250B in cash, 391.2B in revenue, and a 150% ROE, far surpassing industry averages.
""",
    "eps_narrative": """
Generate an EPS growth narration for {ticker} in plain text. Summarize quarterly EPS trends and drivers using the data: {data}. Keep it concise (30-50 words).
Example:
{ticker}'s quarterly EPS over 5 years shows a 12% increase in Q1 2025 driven by services and iPhone sales.
""",
    "market_sentiment": """
Generate a market sentiment narration for {ticker} in plain text. Discuss price, analyst ratings, RSI, and support/resistance using the data: {data}. Keep it concise (50-75 words).
Example:
{ticker} trades at 122 with a bullish trend. Analyst consensus is Buy (2.2/5 rating, 135 target). An overbought RSI (72) suggests a pullback to 110, with support at 100.
""",
    "volatility_narrative": """
Generate a volatility narration for {ticker} in plain text. Discuss volatility indicators and trends using the data: {data}. Keep it concise (30-50 words).
Example:
{ticker} shows rising volatility, with a 14-day ATR of 3.2 and expanding Bollinger Width, suggesting potential price swings.
""",
    "price_levels_narrative": """
Generate a price levels narration for {ticker} in plain text. Highlight current price, support, and resistance using the data: {data}. Keep it concise (30-50 words).
Example:
{ticker}'s key price levels include a current price of 122, support at 100, and resistance at 137, guiding trading strategies.
""",
    "candlestick_narrative": """
Generate a candlestick chart narration for {ticker} in plain text. Describe the 6-month price movement and indicators using the data: {data}. Keep it concise (30-50 words).
Example:
{ticker}'s 6-month price movement includes RSI, volume, and Bollinger Bands, highlighting resistance at 137 and support at 100.
""",
    "recommendations": """
Generate a recommendations narration for {ticker} in plain text. Provide investment advice based on fundamentals, valuation, and technicals using the data: {data}. Keep it concise (100-150 words).
Example:
{ticker} exhibits strong fundamentals with a 31% profit margin and consistent outperformance (18% YTD). Despite a premium valuation (P/E 36.2), its innovation supports long-term growth. Consider holding or buying on dips to 110-100.
"""
}