# Yes, you can replace your main `stock_analyzer.py` file with the following complete version:

import streamlit as st
import requests
import plotly.graph_objs as go
from datetime import datetime
import pandas as pd
import os

# --- CONFIG ---
FINNHUB_API_KEY = st.secrets["FINNHUB_API_KEY`"]
BASE_URL = "https://finnhub.io/api/v1"

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Saini Family Stock Analyzer", layout="wide")
st.title("📊 Saini Family Stock Analyzer")

# --- INPUTS ---
ticker = st.text_input("Enter Stock Ticker (e.g. AAPL)", "AAPL")
hold_months = st.slider("Planned Holding Period (in months)", min_value=1, max_value=120, value=12)

# --- UTILITY FUNCTIONS ---
def get_json(endpoint):
    url = f"{BASE_URL}/{endpoint}&token={FINNHUB_API_KEY}" if "?" in endpoint else f"{BASE_URL}/{endpoint}?token={FINNHUB_API_KEY}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else None

def get_profile(ticker):
    return get_json(f"stock/profile2?symbol={ticker}")

def get_quote(ticker):
    return get_json(f"quote?symbol={ticker}")

def get_peers(ticker):
    return get_json(f"stock/peers?symbol={ticker}")

def get_metrics(ticker):
    return get_json(f"stock/metric?symbol={ticker}&metric=all")

def get_chart_data(ticker):
    now = int(datetime.now().timestamp())
    year_ago = now - 365 * 24 * 60 * 60
    data = get_json(f"stock/candle?symbol={ticker}&resolution=D&from={year_ago}&to={now}")
    if data and data.get("s") == "ok":
        return pd.DataFrame({"Date": pd.to_datetime(data["t"], unit="s"), "Close": data["c"]})
    return None

def compute_score(metrics):
    score = 0
    try:
        if float(metrics['metric']['peBasicExclExtraTTM']) < 25: score += 1
        if float(metrics['metric']['roeTTM']) > 0.15: score += 1
        if float(metrics['metric']['currentRatioTTM']) > 1.5: score += 1
        if float(metrics['metric']['netProfitMarginTTM']) > 0.1: score += 1
        if float(metrics['metric']['debtEquityRatioTTM']) < 1: score += 1
    except:
        pass
    return int(score / 5 * 100)

def risk_rating(metrics):
    try:
        beta = float(metrics['metric'].get('beta', 1))
        debt_eq = float(metrics['metric'].get('debtEquityRatioTTM', 0))
        if beta < 1 and debt_eq < 1: return "🟢 Low"
        elif beta < 1.5 or debt_eq < 2: return "🟡 Medium"
        else: return "🔴 High"
    except:
        return "⚪ Unknown"

# --- MAIN LOGIC ---
if ticker:
    st.subheader(f"🔍 Analyzing {ticker.upper()}")

    profile = get_profile(ticker)
    quote = get_quote(ticker)
    peers = get_peers(ticker)
    metrics = get_metrics(ticker)
    chart_df = get_chart_data(ticker)

    if profile and quote and metrics:
        col1, col2 = st.columns([1, 2])

        with col1:
            st.image(profile.get("logo"), width=100)
            st.metric("Company Name", profile.get("name"))
            st.metric("Industry", profile.get("finnhubIndustry"))
            st.metric("Exchange", profile.get("exchange"))
            st.metric("Country", profile.get("country"))

        with col2:
            st.metric("Current Price", f"${quote.get('c', 'N/A')}")
            st.metric("High (Today)", f"${quote.get('h', 'N/A')}")
            st.metric("Low (Today)", f"${quote.get('l', 'N/A')}")
            st.metric("Open", f"${quote.get('o', 'N/A')}")

        st.markdown(f"🕒 **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        st.divider()

        # Score & risk
        confidence = compute_score(metrics)
        st.subheader("📊 Scoreboard")
        st.progress(confidence / 100)
        st.success(f"✅ Score: {confidence}%")
        st.warning(f"🚦 Risk Level: {risk_rating(metrics)}")

        # Chart
        if chart_df is not None:
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_df['Date'], y=chart_df['Close'], mode='lines', name='Close'))
            fig.update_layout(title=f"📈 1-Year Price Chart for {ticker}", xaxis_title="Date", yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True)

        # Ratios table
        st.subheader("🧮 Financial Metrics")
        ratio_labels = {
            "peBasicExclExtraTTM": "P/E Ratio",
            "roeTTM": "Return on Equity (ROE)",
            "currentRatioTTM": "Current Ratio",
            "netProfitMarginTTM": "Profit Margin",
            "debtEquityRatioTTM": "Debt/Equity"
        }
        rows = []
        for key, label in ratio_labels.items():
            value = metrics['metric'].get(key, "N/A")
            rows.append((label, value))
        df = pd.DataFrame(rows, columns=["Metric", "Value"])
        st.dataframe(df, use_container_width=True)

        st.download_button("📥 Download Metrics as CSV", df.to_csv(index=False), "metrics.csv")

        # Peers
        if peers:
            st.subheader("👥 Peer Comparison")
            st.write(", ".join(peers))

        # Learning section
        with st.expander("📘 Learn Basic Stock Terms"):
            st.markdown("""
            - **P/E Ratio**: Price-to-earnings, lower can mean better value.
            - **ROE**: Return on Equity, shows how profitable a company is.
            - **Current Ratio**: If it's above 1, the company can pay its short-term bills.
            - **Profit Margin**: How much profit the company keeps from each dollar.
            - **Debt/Equity**: Shows if the company is borrowing too much.
            """)

        st.caption(f"⏳ Planned Holding Period: {hold_months} months")

    else:
        st.error("Couldn't load stock data. Please check the ticker or try again later.")
