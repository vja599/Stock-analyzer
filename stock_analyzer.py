import streamlit as st
import plotly.graph_objs as go
import requests
import datetime

# ====================== CONFIG ======================
BASE_URL = "https://finnhub.io/api/v1"
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY"]

# ====================== HELPERS ======================
def get_json(endpoint, params=None):
    if params is None:
        params = {}
    params["token"] = FINNHUB_API_KEY
    url = f"{BASE_URL}/{endpoint}"
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def get_current_price(ticker):
    data = get_json(f"quote?symbol={ticker}")
    if data and all(key in data for key in ["c", "h", "l"]):
        return {
            "current": float(data["c"]),
            "high": float(data["h"]),
            "low": float(data["l"]),
        }
    return None

def get_stock_candles(ticker, months):
    end = int(datetime.datetime.now().timestamp())
    start = int((datetime.datetime.now() - datetime.timedelta(days=30 * months)).timestamp())
    params = {
        "symbol": ticker,
        "resolution": "D",
        "from": start,
        "to": end
    }
    data = get_json("stock/candle", params)
    if data and data.get("s") == "ok":
        return data
    return None

# ====================== UI LAYOUT ======================
st.title("📈 Stock Analyzer with Target Price")

ticker = st.text_input("Enter a stock ticker:", "AAPL").upper()
months = st.slider("Select data range (in months):", 1, 120, 6)

if ticker:
    # 🎯 Target Price Section
    st.subheader("🎯 Set Your Target Buy Price")
    target_price = st.number_input(f"Enter your target buy price for {ticker}:", min_value=0.0, step=0.01)

    price_info = get_current_price(ticker)
    if price_info:
        current = price_info["current"]
        high = price_info["high"]
        low = price_info["low"]

        st.write(f"Current Price: **${current:.2f}**")
        st.write(f"Day's High: **${high:.2f}**, Day's Low: **${low:.2f}**")
        st.write(f"Your Target Buy Price: **${target_price:.2f}**")

        if current <= target_price:
            st.success("✅ The stock is at or below your target buy price!")
        else:
            st.info("📉 The stock is still above your target. Keep watching!")
    else:
        st.warning("⚠️ Couldn't retrieve current price data. Try again later.")

    # 📊 Interactive Line Chart Section
    st.subheader("📉 Stock Price History")
    candles = get_stock_candles(ticker, months)
    if candles:
        dates = [datetime.datetime.fromtimestamp(ts) for ts in candles["t"]]
        prices = candles["c"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=prices, mode='lines', name='Close Price'))
        fig.update_layout(title=f"{ticker} Stock Price - Last {months} Months",
                          xaxis_title='Date',
                          yaxis_title='Price (USD)',
                          template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Failed to load stock chart data.")
