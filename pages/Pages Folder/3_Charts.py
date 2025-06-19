import streamlit as st
import requests
import datetime

API_KEY = "CZAQTT5zmTJHYqfNV3PoYaiBTUhjdpnO"
BASE_URL = "https://finnhub.io/api/v1"

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

st.title("📈 Historical Charts")
symbol = st.text_input("Enter stock symbol:", "AAPL")
months = st.slider("Select time range (months):", 1, 120, 12)

if symbol:
    data = get_historical_data(symbol, months)
    if data:
        st.line_chart(data['c'])
        st.caption("Closing price over time")
    else:
        st.error("Unable to fetch chart data.")
