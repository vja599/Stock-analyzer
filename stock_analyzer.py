import streamlit as st
import requests
import datetime

# --- Configuration ---
API_KEY = "d19u0q1r01qmm7u1emt0d19u0q1r01qmm7u1emtg"
BASE_URL = "https://finnhub.io/api/v1"

# --- Helper Functions ---
def get_historical_data(symbol, months):
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=30 * months)
    url = f"{BASE_URL}/stock/candle"
    params = {
        "symbol": symbol,
        "resolution": "D",
        "from": int(start_date.timestamp()),
        "to": int(end_date.timestamp()),
        "token": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data if data.get("s") == "ok" else None

def get_current_price(symbol):
    url = f"{BASE_URL}/quote"
    response = requests.get(url, params={"symbol": symbol, "token": API_KEY})
    return response.json().get("c")

def get_fundamentals(symbol):
    url = f"{BASE_URL}/stock/metric"
    response = requests.get(url, params={"symbol": symbol, "metric": "all", "token": API_KEY})
    return response.json().get("metric")

def evaluate_stock(current_price, target_price, pe_ratio, revenue_growth):
    if current_price <= 0 or target_price <= 0:
        return "Invalid inputs", "⚠️", 0

    score = 0
    max_score = 6

    # Price vs Target
    ratio = target_price / current_price
    if ratio >= 1.2:
        score += 2
    elif 0.9 <= ratio < 1.2:
        score += 1

    # P/E Ratio
    if pe_ratio and pe_ratio < 20:
        score += 2
    elif pe_ratio and pe_ratio < 35:
        score += 1

    # Revenue Growth
    if revenue_growth and revenue_growth > 0.10:
        score += 2
    elif revenue_growth and revenue_growth > 0.03:
        score += 1

    confidence = round((score / max_score) * 100)

    if score >= 5:
        return "Strong Buy", "✅", confidence
    elif score >= 3:
        return "Hold", "🤔", confidence
    else:
        return "Avoid", "❌", confidence


    # Price vs Target
    ratio = target_price / current_price
    if ratio >= 1.2:
        score += 2
    elif 0.9 <= ratio < 1.2:
        score += 1

    # P/E Ratio
    if pe_ratio and pe_ratio < 20:
        score += 2
    elif pe_ratio and pe_ratio < 35:
        score += 1

    # Revenue Growth
    if revenue_growth and revenue_growth > 0.10:
        score += 2
    elif revenue_growth and revenue_growth > 0.03:
        score += 1

    if score >= 5:
        return "Strong Buy", "✅"
    elif score >= 3:
        return "Hold", "🤔"
    else:
        return "Avoid", "❌"

# --- Streamlit UI ---
st.set_page_config(page_title="SFSA - Saini Family Stock Analyzer")
st.title("📊 SFSA - Saini Family Stock Analyzer")

symbol = st.text_input("Enter Stock Ticker (e.g., AAPL, MSFT):", "AAPL")
months = st.slider("Select time range for analysis (months):", 1, 120, 12)
target_price = st.number_input("Enter your target buy price ($):", min_value=0.01, value=150.00, step=0.01)

if st.button("Analyze Stock"):
    with st.spinner("Fetching data and evaluating..."):
        current_price = get_current_price(symbol)
        historical_data = get_historical_data(symbol, months)
        fundamentals = get_fundamentals(symbol)

        if current_price is None or historical_data is None or fundamentals is None:
            st.error("Failed to retrieve stock data. Check the ticker symbol or try again later.")
        else:
            pe_ratio = fundamentals.get("peNormalizedAnnual")
            revenue_growth = fundamentals.get("revenueGrowthYearOverYear")

            st.subheader(f"📈 Current Price for {symbol.upper()}: ${current_price:.2f}")
            st.write(f"P/E Ratio: {pe_ratio:.2f}" if pe_ratio else "P/E Ratio: N/A")
            st.write(f"Revenue Growth YoY: {revenue_growth:.2%}" if revenue_growth else "Revenue Growth YoY: N/A")

            recommendation, icon, confidence = evaluate_stock(current_price, target_price, pe_ratio, revenue_growth)
            st.success(f"{icon} **{recommendation}** — Confidence Score: **{confidence}%**")

            

            st.line_chart(historical_data['c'])
            st.caption("Closing price chart over selected period.")
