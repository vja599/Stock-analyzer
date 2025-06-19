import streamlit as st
import requests
import os

# Load API keys from environment variables or defaults
API_KEY = os.getenv("FMP_API_KEY", "YOUR_DEFAULT_API_KEY")
BASE_URL = "https://financialmodelingprep.com/api/v3"

st.set_page_config(page_title="Saini Family Stock Analyzer", layout="wide")
st.title("📊 Saini Family Stock Analyzer")

# User inputs
ticker = st.text_input("Enter Stock Ticker (e.g. AAPL)", "AAPL")
hold_months = st.slider("Planned Holding Period (in months)", min_value=1, max_value=120, value=1)

# Utility functions
def get_json(endpoint):
    url = f"{BASE_URL}/{endpoint}&apikey={API_KEY}" if "?" in endpoint else f"{BASE_URL}/{endpoint}?apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_profile(ticker):
    return get_json(f"profile/{ticker}")

def get_ratios(ticker):
    data = get_json(f"ratios-ttm/{ticker}")
    if not data:
        st.warning("No ratio data returned. Trying alternative endpoint...")
        data = get_json(f"ratios/{ticker}?limit=1")
    return data

def get_quote(ticker):
    return get_json(f"quote/{ticker}")

def get_peers(ticker):
    return get_json(f"stock_peers?symbol={ticker}")

def safe_get(data, key):
    return data[0].get(key) if data and key in data[0] else "N/A"

# Confidence scoring system (optional, but no AI)
def compute_confidence_score(ratios):
    if not ratios:
        return 0
    score = 0
    max_score = 6  # Total possible

    pe_ratio = float(ratios[0].get("peRatioTTM", 0))
    roe = float(ratios[0].get("returnOnEquityTTM", 0))
    current_ratio = float(ratios[0].get("currentRatioTTM", 0))
    debt_equity = float(ratios[0].get("debtEquityRatioTTM", 0))
    profit_margin = float(ratios[0].get("netProfitMarginTTM", 0))
    interest_coverage = float(ratios[0].get("interestCoverageTTM", 0))

    if 5 < pe_ratio < 25:
        score += 1
    if roe > 0.15:
        score += 1
    if current_ratio >= 1.5:
        score += 1
    if debt_equity < 1:
        score += 1
    if profit_margin > 0.1:
        score += 1
    if interest_coverage > 3:
        score += 1

    return int((score / max_score) * 100)

# Main app logic
if ticker:
    st.subheader(f"🔍 Analyzing {ticker.upper()}")

    profile = get_profile(ticker)
    ratios = get_ratios(ticker)
    quote = get_quote(ticker)
    peers = get_peers(ticker)

    if profile and quote:
        col1, col2 = st.columns(2)

        with col1:
            st.image(profile[0].get("image"), width=100)
            st.metric("Company Name", profile[0].get("companyName"))
            st.metric("Industry", profile[0].get("industry"))
            st.metric("Exchange", profile[0].get("exchange"))

        with col2:
            st.metric("Current Price", f"${quote[0].get('price', 'N/A')}")
            st.metric("Market Cap", f"${quote[0].get('marketCap', 'N/A'):,}")
            st.metric("Volume", f"{quote[0].get('volume', 'N/A'):,}")

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
                st.metric(label, safe_get(ratios, key))

            # Show confidence score
            confidence = compute_confidence_score(ratios)
            st.success(f"📊 Confidence Score: {confidence}%")

        else:
            st.warning("Financial ratios not available.")

        st.caption(f"⏳ Holding period: {hold_months} month(s)")

        if peers:
            st.subheader("🧝 Peer Comparison")
            st.write(", ".join(peers.get("peersList", [])))

    else:
        st.error("Failed to retrieve stock data. Please check the ticker symbol.")
