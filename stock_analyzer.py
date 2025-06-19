import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import plotly.graph_objs as go

# ============================
# API Setup
# ============================
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY"]
BASE_URL = "https://finnhub.io/api/v1"

# ============================
# Helper Functions
# ============================
def get_json(endpoint):
    url = f"{BASE_URL}/{endpoint}&token={FINNHUB_API_KEY}" if "?" in endpoint else f"{BASE_URL}/{endpoint}?token={FINNHUB_API_KEY}"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json()
    else:
        return None

def get_stock_profile(ticker):
    return get_json(f"stock/profile2?symbol={ticker}")

def get_quote(ticker):
    return get_json(f"quote?symbol={ticker}")

def get_metrics(ticker):
    return get_json(f"stock/metric?symbol={ticker}&metric=all")

def get_peers(ticker):
    return get_json(f"stock/peers?symbol={ticker}")

def get_historical_chart_data(ticker, months):
    now = int(datetime.now().timestamp())
    from_time = now - int(months * 30.5 * 24 * 60 * 60)
    data = get_json(f"stock/candle?symbol={ticker}&resolution=D&from={from_time}&to={now}")
    if data and data.get("s") == "ok":
        return pd.DataFrame({"Date": pd.to_datetime(data["t"], unit="s"), "Close": data["c"]})
    return None

# ============================
# Streamlit App
# ============================
st.set_page_config(page_title="📊 Stock Analyzer", layout="wide")
st.title("📈 Advanced Stock Analyzer")

# User Input
ticker = st.text_input("Enter stock ticker (e.g., AAPL, MSFT, TSLA):").upper().strip()

if ticker:
    # Fetch data
    profile = get_stock_profile(ticker)
    quote = get_quote(ticker)
    metrics = get_metrics(ticker)
    peers = get_peers(ticker)

    if profile and quote:
        st.subheader(f"📌 {profile.get('name', ticker)} ({ticker})")
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Current Price", f"${quote['c']:.2f}")
            st.metric("High Today", f"${quote['h']:.2f}")
            st.metric("Low Today", f"${quote['l']:.2f}")

        with col2:
            st.metric("Previous Close", f"${quote['pc']:.2f}")
            st.metric("Open Price", f"${quote['o']:.2f}")
            st.metric("Change", f"{quote['d']:.2f} ({quote['dp']:.2f}%)")

        # Show financial metrics
        if metrics:
            st.subheader("📊 Key Financial Metrics")
            m = metrics.get("metric", {})
            st.write({
                "PE Ratio": m.get("peBasicExclExtraTTM"),
                "PB Ratio": m.get("pbAnnual"),
                "ROE": m.get("roeRfy"),
                "ROA": m.get("roaRfy"),
                "Debt/Equity": m.get("totalDebt/totalEquityAnnual"),
                "Market Cap": m.get("marketCapitalization")
            })

        # Interactive chart
        st.subheader("📈 Interactive Stock Price Chart")
        hist_months = st.slider("Select chart range (in months)", 1, 120, 12)
        hist_data = get_historical_chart_data(ticker, hist_months)

        if hist_data is not None:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist_data['Date'], y=hist_data['Close'], mode='lines', name='Close'))
            fig.update_layout(title=f"{ticker.upper()} Price - Last {hist_months} Months", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not load chart data.")

        # Peers
        if peers:
            st.subheader("🔍 Peer Comparison")
            st.write(peers)
    else:
        st.error("❌ Failed to retrieve stock data. Please check the ticker symbol.")
