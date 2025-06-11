import yfinance as yf
import finnhub
import pandas as pd
from datetime import datetime, timedelta
import pytz
import uuid
import json
import streamlit as st
from dotenv import load_dotenv
import os
from narration import bedrock_runtime, MODEL_ID

# Load environment variables
load_dotenv()

# Configuration
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")
TWO_MONTHS_AGO = (datetime.now(pytz.UTC) - timedelta(days=60)).strftime("%Y-%m-%d")
TODAY = datetime.now(pytz.UTC).strftime("%Y-%m-%d")
IST = pytz.timezone("Asia/Kolkata")
MAX_NEWS_ITEMS = 30

def clean_text(text):
    """Remove $ and markdown italics from text."""
    if not isinstance(text, str):
        return text
    text = text.replace("$", "").replace("_", "").replace("*", "")
    return text

def fetch_yahoo_finance_news(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        news_items = ticker.news
        yahoo_news = []
        for item in news_items:
            publish_time_str = item.get("pubDate") or item.get("displayTime")
            if not publish_time_str:
                continue
            title = clean_text(item.get("title", "No title"))
            if title == "No title":
                continue
            try:
                publish_time = datetime.strptime(publish_time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
                if publish_time >= datetime.now(pytz.UTC) - timedelta(days=60):
                    summary = clean_text(item.get("summary") or item.get("description") or title)
                    summary = summary[:100] + "..." if len(summary) > 100 else summary
                    yahoo_news.append({
                        "id": str(uuid.uuid4()),
                        "date": publish_time,
                        "title": title,
                        "summary": summary,
                        "source": "Yahoo Finance",
                        "url": item.get("clickThroughUrl", {}).get("url") or item.get("canonicalUrl", {}).get("url", "No link")
                    })
            except (ValueError, TypeError):
                continue
        return yahoo_news
    except Exception:
        return []

def fetch_finnhub_news(ticker_symbol, api_key):
    try:
        finnhub_client = finnhub.Client(api_key=api_key)
        news_items = finnhub_client.company_news(ticker_symbol, _from=TWO_MONTHS_AGO, to=TODAY)
        finnhub_news = []
        for item in news_items:
            publish_time = item.get("datetime")
            if not publish_time:
                continue
            title = clean_text(item.get("headline", "No title"))
            if title == "No title":
                continue
            try:
                publish_time = datetime.fromtimestamp(publish_time, tz=pytz.UTC)
                if publish_time >= datetime.now(pytz.UTC) - timedelta(days=60):
                    summary = clean_text(item.get("summary", "No summary available"))
                    summary = summary if summary and summary != "No summary available" else title[:100] + "..."
                    finnhub_news.append({
                        "id": str(uuid.uuid4()),
                        "date": publish_time,
                        "title": title,
                        "summary": summary,
                        "source": "Finnhub",
                        "url": item.get("url", "No link")
                    })
            except (TypeError, ValueError):
                continue
        return finnhub_news
    except Exception:
        return []

def fetch_news(ticker):
    if not ticker:
        return None
    yahoo_news = fetch_yahoo_finance_news(ticker)
    finnhub_news = fetch_finnhub_news(ticker, FINNHUB_API_KEY)
    all_news = yahoo_news + finnhub_news
    all_news = sorted(all_news, key=lambda x: x["date"], reverse=True)[:MAX_NEWS_ITEMS]
    
    if not all_news:
        return None
    
    news_df = pd.DataFrame(all_news)
    news_df['date'] = pd.to_datetime(news_df['date'], utc=True)
    news_df['date_ist'] = news_df['date'].dt.tz_convert(IST).dt.strftime("%Y-%m-%d %H:%M:%S")
    news_df['date'] = news_df['date'].dt.strftime("%Y-%m-%d %H:%M:%S")
    news_df = news_df[['id', 'date', 'date_ist', 'title', 'summary', 'source', 'url']]
    return news_df

def process_news_with_llm(news_df):
    if news_df is None or news_df.empty:
        return None
    news_data = news_df[["id", "title", "summary"]].to_dict(orient="records")
    news_json = json.dumps(news_data, indent=2)
    
    prompt = f"""
    You are an AI assistant analyzing news articles for a stock. Below is a JSON list of news items, each with an 'id', 'title', and 'summary'. Your task is to:

    1. Identify 4–6 key findings or themes from the news (e.g., AI developments, stock performance, product launches).
    2. Group the news items by relevance to each finding, using their 'id'.
    3. Output a JSON object where each key is a finding (descriptive name, no $ or markdown) and each value is a list of news IDs relevant to that finding.

    Ensure the output is in the format:
    {{"finding1": ["id1", "id2"], "finding2": ["id3", "id4"], ...}}

    News data:
    {news_json}
    """
    
    messages = [{"role": "user", "content": [{"text": prompt}]}]
    
    try:
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            system=[{"text": "You are an expert financial analyst summarizing news themes. Format monetary values without currency symbols (e.g., 1.00 instead of $1.00)."}],
            inferenceConfig={"maxTokens": 2000, "temperature": 0.7}
        )
        llm_output = response["output"]["message"]["content"][0]["text"]
        
        start_idx = llm_output.find("{")
        end_idx = llm_output.rfind("}") + 1
        if start_idx == -1 or end_idx == 0:
            return None
        findings = json.loads(llm_output[start_idx:end_idx])
        cleaned_findings = {clean_text(k): v for k, v in findings.items()}
        return cleaned_findings
    except Exception as e:
        st.warning(f"Failed to process news with LLM: {e}")
        return None