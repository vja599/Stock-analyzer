import streamlit as st
import requests
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime, timedelta

# Load your Finnhub API key securely from Streamlit secrets
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY"]  # Add this to your .streamlit/secrets.toml file

st.set_page_config(page_title="Saini Family Stock Analyzer", layout="wide")
st.title("📊 Saini Family Stock Analyzer")

# User inputs
ticker = st.text_input("Enter Stock Ticker (e.g. AAPL)", "AAPL")
hold_months = st.slider("Planned Holding Period (in months)", min_value=1, max_value=120, value=1)
chart_months = st.slider("Chart Time Range (in months)", min_value=1, max_value=120, value=6)

# Utility functions using Finnhub
def get_quote(ticker):
    url = f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_profile(ticker):
    url = f"https://finnhub.io/api/v1/stock/profile2?symbol={ticker}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_peers(ticker):
    url = f"https://finnhub.io/api/v1/stock/peers?symbol={ticker}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def get_candles(ticker, months):
    end = int(datetime.now().timestamp())
    start = int((datetime.now() - timedelta(days=30 * months)).timestamp())
    url = f"https://finnhub.io/api/v1/stock/candle?symbol={ticker}&resolution=D&from={start}&to={end}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("s") == "ok":
            df = pd.DataFrame({
                "Date": pd.to_datetime(data["t"], unit='s'),
                "Open": data["o"],
                "High": data["h"],
                "Low": data["l"],
                "Close": data["c"],
                "Volume": data["v"]
            })
            return df
    return None

def compute_score(quote):
    score = 0
    max_score = 3

    if quote.get("c", 0) > quote.get("pc", 0):
        score += 1  # Current price is higher than previous close
    if quote.get("h", 0) - quote.get("l", 0) > 0:
        score += 1  # Price range exists
    if quote.get("c", 0) != 0:
        score += 1  # Stock is active

    return int((score / max_score) * 100)

# Main app logic
if ticker:
    st.subheader(f"🔍 Analyzing {ticker.upper()}")

    profile = get_profile(ticker)
    quote = get_quote(ticker)
    peers = get_peers(ticker)
    chart_data = get_candles(ticker, chart_months)

    if profile and quote:
        col1, col2 = st.columns(2)

        with col1:
            st.image(profile.get("logo"), width=100)
            st.metric("Company Name", profile.get("name", "N/A"))
            st.metric("Industry", profile.get("finnhubIndustry", "N/A"))
            st.metric("Exchange", profile.get("exchange", "N/A"))

        with col2:
            st.metric("Current Price", f"${quote.get('c', 'N/A')}")
            st.metric("High Price", f"${quote.get('h', 'N/A')}")
            st.metric("Low Price", f"${quote.get('l', 'N/A')}")
            score = compute_score(quote)
            st.metric("Stock Score", f"{score}%")

        st.divider()

        st.caption(f"⏳ Holding period: {hold_months} month(s)")

        if chart_data is not None:
            st.subheader(f"📉 Price Chart ({chart_months} Months)")
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=chart_data["Date"],
                open=chart_data["Open"],
                high=chart_data["High"],
                low=chart_data["Low"],
                close=chart_data["Close"],
                name="Candlestick"
            ))
            fig.update_layout(title=f"{ticker.upper()} Candlestick Chart", xaxis_title="Date", yaxis_title="Price (USD)")
            st.plotly_chart(fig, use_container_width=True)

        if peers:
            st.subheader("🧝 Peer Comparison")
            st.write(", ".join(peers))

        st.markdown("""
        ### 🧠 Stock Market Basics
        - **Ticker**: A symbol representing a publicly traded company.
        - **Current Price**: The most recent trading price.
        - **High/Low**: Highest and lowest prices during a trading session.
        - **Peers**: Other companies in the same sector or industry.
        - **Candlestick/Line Chart**: Visual representation of stock price over time.
        - **Stock Score**: A basic quality score based on activity and pricing trend.
        """)

    else:
        st.error("Failed to retrieve stock data. Please check the ticker symbol.")
