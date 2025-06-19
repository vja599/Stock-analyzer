import streamlit as st
import requests

API_KEY = "CZAQTT5zmTJHYqfNV3PoYaiBTUhjdpnO"
BASE_URL = "https://finnhub.io/api/v1"

def get_fundamentals(symbol):
    url = f"{BASE_URL}/stock/metric"
    params = {
        "symbol": symbol,
        "metric": "all",
        "token": API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("metric")

st.title("📂 Fundamentals Overview")
symbol = st.text_input("Enter stock symbol:", "AAPL")

if symbol:
    metrics = get_fundamentals(symbol)

    if metrics:
        st.subheader(f"Fundamental Metrics for {symbol.upper()}")
        st.write(f"**Revenue Growth YoY:** {metrics.get('revenueGrowthYearOverYear', 'N/A')}")
        st.write(f"**Net Profit Margin:** {metrics.get('netProfitMarginAnnual', 'N/A')}")
        st.write(f"**Return on Equity (ROE):** {metrics.get('roeAnnual', 'N/A')}")
        st.write(f"**Debt-to-Equity Ratio:** {metrics.get('debtEquityRatio', 'N/A')}")
        st.write(f"**Earnings Per Share (EPS):** {metrics.get('epsAnnual', 'N/A')}")
    else:
        st.error("Unable to fetch fundamental metrics.")
