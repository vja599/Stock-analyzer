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

st.title("💰 Valuation Analysis")
symbol = st.text_input("Enter stock symbol:", "AAPL")

if symbol:
    metrics = get_fundamentals(symbol)

    if metrics:
        st.subheader(f"Valuation Metrics for {symbol.upper()}")
        st.write(f"**P/E Ratio:** {metrics.get('peNormalizedAnnual', 'N/A')}")
        st.write(f"**Price-to-Book (P/B):** {metrics.get('pbAnnual', 'N/A')}")
        st.write(f"**Price-to-Sales (P/S):** {metrics.get('psAnnual', 'N/A')}")
        st.write(f"**EV/EBITDA:** {metrics.get('evToEbitdaAnnual', 'N/A')}")
    else:
        st.error("Unable to fetch valuation metrics.")
