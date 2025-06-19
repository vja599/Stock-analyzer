import streamlit as st
import pandas as pd
import datetime
import requests

# Set page config
st.set_page_config(page_title="Stock Analyzer", layout="centered")

# Your FMP API Key
FMP_API_KEY = "CZAQTT5zmTJHYqfNV3PoYaiBTUhjdpnO"

# Fetch company profile and financials from FMP
def fetch_financials(ticker):
    profile_url = f"https://financialmodelingprep.com/api/v3/profile/{ticker}?apikey={FMP_API_KEY}"
    metrics_url = f"https://financialmodelingprep.com/api/v3/key-metrics-ttm/{ticker}?apikey={FMP_API_KEY}"
    ratios_url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={FMP_API_KEY}"
    income_url = f"https://financialmodelingprep.com/api/v3/income-statement/{ticker}?limit=1&apikey={FMP_API_KEY}"
    cashflow_url = f"https://financialmodelingprep.com/api/v3/cash-flow-statement/{ticker}?limit=1&apikey={FMP_API_KEY}"

    try:
        profile = requests.get(profile_url).json()[0]
        metrics = requests.get(metrics_url).json()[0]
        ratios = requests.get(ratios_url).json()[0]
        income = requests.get(income_url).json()[0]
        cashflow = requests.get(cashflow_url).json()[0]

        return {
            "name": profile.get("companyName"),
            "sector": profile.get("sector"),
            "industry": profile.get("industry"),
            "market_cap": profile.get("mktCap"),
            "pe_ratio": profile.get("pe"),
            "forward_pe": metrics.get("peRatio"),
            "peg_ratio": ratios.get("pegRatio"),
            "eps": profile.get("eps"),
            "debt_to_equity": ratios.get("debtEquityRatio"),
            "revenue_growth": metrics.get("revenueGrowth"),
            "net_income": income.get("netIncome"),
            "return_on_equity": ratios.get("returnOnEquity"),
            "free_cashflow": cashflow.get("freeCashFlow"),
            "beta": profile.get("beta"),
            "price": profile.get("price"),
            "dividend_yield": profile.get("lastDiv") / profile.get("price") if profile.get("lastDiv") else 0
        }
    except Exception as e:
        st.error(f"❌ Error fetching data: {e}")
        return None

# Get historical price chart
def get_price_history(ticker, period="1y"):
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{ticker}?serietype=line&apikey={FMP_API_KEY}"
    data = requests.get(url).json()
    if "historical" in data:
        df = pd.DataFrame(data["historical"])
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        return df
    return pd.DataFrame()

# Scoring logic
def evaluate_stock(financials):
    score = 0
    reasons = []

    if financials['eps'] and financials['eps'] > 0:
        score += 15
        reasons.append("✅ Positive EPS indicates profitability.")
    if financials['return_on_equity'] and financials['return_on_equity'] > 0.10:
        score += 10
        reasons.append("✅ ROE > 10% shows strong management.")
    if financials['revenue_growth'] and financials['revenue_growth'] > 0.10:
        score += 15
        reasons.append("✅ Revenue growth > 10%.")
    if financials['debt_to_equity'] and financials['debt_to_equity'] < 1:
        score += 10
        reasons.append("✅ Low debt-to-equity ratio.")
    if financials['pe_ratio'] and financials['pe_ratio'] < 20:
        score += 10
        reasons.append("✅ P/E ratio < 20 may indicate undervaluation.")
    if financials['dividend_yield'] and financials['dividend_yield'] > 0.02:
        score += 5
        reasons.append("✅ Healthy dividend yield.")

    return min(score, 100), reasons

def evaluate_price_target(current_price, target_price):
    if not current_price:
        return "❓ Current price unavailable.", False
    diff = (target_price - current_price) / current_price * 100
    if diff > 10:
        return f"⚠️ Target price is **{diff:.2f}% ABOVE** current price — might want to wait.", False
    elif diff < -10:
        return f"✅ Target price is **{abs(diff):.2f}% BELOW** current price — may be a strong buy.", True
    else:
        return f"📉 Target is close to current price ({diff:.2f}%).", True

def format_metric(label, value, threshold, higher_is_better=True):
    if value is None:
        return f"{label}: ❓ N/A"
    is_good = (value > threshold) if higher_is_better else (value < threshold)
    emoji = "🟢" if is_good else "🔴"
    return f"{emoji} **{label}:** {value:.2f}"

# Streamlit app UI
st.title("📈 Saini Family Stock Analyzer")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)").upper()
target_price = st.number_input("What price would you like to buy at? ($)", min_value=0.0, step=0.01)
hold_months = st.slider("📆 Holding Period (in months)", min_value=1, max_value=120, value=1, step=1)

if st.button("Analyze Stock"):
    with st.spinner("Fetching financials..."):
        financials = fetch_financials(ticker)
        if financials:
            score, reasons = evaluate_stock(financials)
            price_eval, good_price = evaluate_price_target(financials["price"], target_price)
            price_history = get_price_history(ticker)

            st.subheader(f"📊 {financials['name']} ({ticker})")
            st.write(f"Sector: **{financials['sector']}**, Industry: **{financials['industry']}**")

            if financials['price']:
                st.metric("Current Price", f"${financials['price']:.2f}")
            st.metric("Your Target Price", f"${target_price:.2f}")
            st.info(price_eval)

            st.subheader("📈 Price History (1 Year)")
            if not price_history.empty:
                st.line_chart(price_history['close'])
            else:
                st.warning("No price history available.")

            st.subheader("📌 Score & Recommendation")
            st.write(f"**Score:** {score}/100")
            if score >= 75:
                st.success("✅ Strong Buy")
            elif score >= 60:
                st.success("🟢 Buy")
            elif score >= 40:
                st.warning("🟡 Hold")
            else:
                st.error("❌ Avoid")

            st.subheader("📋 Reasons")
            for reason in reasons:
                st.write(f"- {reason}")

            st.subheader("🔎 Key Metrics")
            st.markdown(format_metric("EPS", financials['eps'], 0))
            st.markdown(format_metric("ROE", financials['return_on_equity'], 0.10))
            st.markdown(format_metric("Revenue Growth", financials['revenue_growth'], 0.10))
            st.markdown(format_metric("Debt/Equity", financials['debt_to_equity'], 1, higher_is_better=False))
            st.markdown(format_metric("P/E Ratio", financials['pe_ratio'], 20, higher_is_better=False))
            st.markdown(format_metric("Dividend Yield", financials['dividend_yield'], 0.02))
            st.markdown(format_metric("PEG Ratio", financials['peg_ratio'], 1, higher_is_better=False))
            st.markdown(format_metric("Forward P/E", financials['forward_pe'], 20, higher_is_better=False))

            st.caption(f"⏳ Holding period: {hold_years} year(s)")

            st.subheader("📁 Save Your Analysis")
            result = {
                "ticker": ticker,
                "score": score,
                "price": financials["price"],
                "target_price": target_price,
                "recommendation": (
                    "Strong Buy" if score >= 75 else "Buy" if score >= 60 else "Hold" if score >= 40 else "Avoid"
                ),
                "date": datetime.date.today().isoformat()
            }
            st.download_button("Download Result", str(result), file_name=f"{ticker}_analysis.txt")
