import streamlit as st
import requests
from datetime import datetime

# Load API key securely from Streamlit secrets
API_KEY = st.secrets.get("FMP_API_KEY", "YOUR_DEFAULT_API_KEY")
BASE_URL = "https://financialmodelingprep.com/api/v3"

# Configure Streamlit page
st.set_page_config(page_title="Saini Family Stock Analyzer", layout="wide")
st.title("📊 Saini Family Stock Analyzer")

# User inputs
ticker = st.text_input("Enter Stock Ticker (e.g. AAPL)", "AAPL")
hold_months = st.slider("Planned Holding Period (in months)", 1, 120, 1)

# Utility functions
def get_json(endpoint):
    url = f"{BASE_URL}/{endpoint}&apikey={API_KEY}" if "?" in endpoint else f"{BASE_URL}/{endpoint}?apikey={API_KEY}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None

def safe_get(data, key):
    try:
        return data[0].get(key, "N/A")
    except:
        return "N/A"

def format_percent(value):
    try:
        return f"{float(value):.2%}"
    except:
        return "N/A"

def compute_confidence_score(ratios):
    if not ratios:
        return 0
    score = 0
    max_score = 6

    def to_float(val): 
        try: return float(val)
        except: return 0

    pe_ratio = to_float(ratios[0].get("peRatioTTM"))
    roe = to_float(ratios[0].get("returnOnEquityTTM"))
    current_ratio = to_float(ratios[0].get("currentRatioTTM"))
    debt_equity = to_float(ratios[0].get("debtEquityRatioTTM"))
    profit_margin = to_float(ratios[0].get("netProfitMarginTTM"))
    interest_coverage = to_float(ratios[0].get("interestCoverageTTM"))

    if 5 < pe_ratio < 25: score += 1
    if roe > 0.15: score += 1
    if current_ratio >= 1.5: score += 1
    if debt_equity < 1: score += 1
    if profit_margin > 0.1: score += 1
    if interest_coverage > 3: score += 1

    return int((score / max_score) * 100)

# Fetch data
profile = get_json(f"profile/{ticker}")
ratios = get_json(f"ratios-ttm/{ticker}")
quote = get_json(f"quote/{ticker}")
peers = get_json(f"stock_peers?symbol={ticker}")

# Render content
if ticker and profile and quote:
    st.subheader(f"🔍 Analyzing {ticker.upper()}")
    col1, col2 = st.columns(2)

    with col1:
        st.image(profile[0].get("image"), width=100)
        st.metric("Company Name", profile[0].get("companyName"))
        st.metric("Industry", profile[0].get("industry"))
        st.metric("Exchange", profile[0].get("exchange"))

    with col2:
        st.metric("Current Price", f"${quote[0].get('price', 'N/A')}")
        st.metric("Market Cap", f"${quote[0].get('marketCap', 0):,}")
        st.metric("Volume", f"{quote[0].get('volume', 0):,}")

        # Show last updated timestamp
        ts = quote[0].get("timestamp")
        if ts:
            st.caption(f"📅 Last Updated: {datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')}")

    st.divider()
    st.subheader("📈 Saini Metrics")

    if ratios:
        metrics = {
            "P/E Ratio": "peRatioTTM",
            "Return on Equity (ROE)": "returnOnEquityTTM",
            "Current Ratio": "currentRatioTTM",
            "Debt/Equity Ratio": "debtEquityRatioTTM",
            "Profit Margin": "netProfitMarginTTM",
            "Interest Coverage Ratio": "interestCoverageTTM"
        }

        for label, key in metrics.items():
            value = safe_get(ratios, key)
            display = format_percent(value) if "Margin" in label or "ROE" in label else value
            st.metric(label, display)

        confidence = compute_confidence_score(ratios)
        if confidence >= 80:
            st.success(f"📊 Confidence Score: {confidence}%")
        elif confidence >= 50:
            st.warning(f"📊 Confidence Score: {confidence}%")
        else:
            st.error(f"📊 Confidence Score: {confidence}%")

        # Fair value estimate (basic)
        price = quote[0].get("price")
        pe_ratio = float(ratios[0].get("peRatioTTM", 0))
        if price and pe_ratio:
            est_fair_value = float(price) / pe_ratio * 15
            st.metric("🎯 Estimated Fair Value (PE=15)", f"${est_fair_value:.2f}")

    else:
        st.warning("Financial ratios not available.")

    st.caption(f"⏳ Holding period: {hold_months} month(s)")

    if peers:
        st.subheader("🧭 Peer Comparison")
        st.write(", ".join(peers.get("peersList", [])))

else:
    st.error("❌ Failed to retrieve stock data. Please check the ticker symbol.")
