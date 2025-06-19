# =======================
# 📊 Stock Analyzer Web App
# =======================

import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import json

# Page Configuration
st.set_page_config(page_title="Stock Analyzer", layout="centered")

# =======================
# 🔧 Utility Functions
# =======================

def fetch_financials(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    return {
        "name": info.get("longName", "N/A"),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap", 0),
        "pe_ratio": info.get("trailingPE", None),
        "forward_pe": info.get("forwardPE", None),
        "peg_ratio": info.get("pegRatio", None),
        "eps": info.get("trailingEps", None),
        "debt_to_equity": info.get("debtToEquity", None),
        "revenue_growth": info.get("revenueGrowth", None),
        "net_income": info.get("netIncomeToCommon", None),
        "return_on_equity": info.get("returnOnEquity", None),
        "free_cashflow": info.get("freeCashflow", None),
        "beta": info.get("beta", None),
        "price": info.get("currentPrice", None),
        "dividend_yield": info.get("dividendYield", 0)
    }

def get_price_history(ticker, period="1y"):
    return yf.Ticker(ticker).history(period=period)

def evaluate_stock(financials):
    score, reasons = 0, []

    checks = [
        (financials['eps'] > 0, 15, "✅ Positive EPS indicates profitability."),
        (financials['return_on_equity'] and financials['return_on_equity'] > 0.10, 10, "✅ ROE > 10% shows strong management."),
        (financials['revenue_growth'] and financials['revenue_growth'] > 0.10, 15, "✅ Revenue growth > 10%."),
        (financials['debt_to_equity'] and financials['debt_to_equity'] < 1, 10, "✅ Low debt-to-equity ratio."),
        (financials['pe_ratio'] and financials['pe_ratio'] < 20, 10, "✅ P/E ratio < 20 may indicate undervaluation."),
        (financials['dividend_yield'] and financials['dividend_yield'] > 0.02, 5, "✅ Healthy dividend yield."),
    ]

    for condition, pts, reason in checks:
        if condition:
            score += pts
            reasons.append(reason)

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

def get_recommendation(score):
    if score >= 75:
        return "✅ Strong Buy"
    elif score >= 60:
        return "🟢 Buy"
    elif score >= 40:
        return "🟡 Hold"
    else:
        return "❌ Avoid"

# =======================
# 🚀 Streamlit UI
# =======================

st.title("📈 Stock Analyzer Web App")

ticker = st.text_input("Enter Stock Ticker (e.g., AAPL)").upper()
target_price = st.number_input("Target Buy Price ($)", min_value=0.0, step=0.01)
hold_months = st.slider("Holding Period (months)", 1, 24, 3)

if st.button("Analyze Stock"):
    with st.spinner("Fetching and analyzing..."):
        try:
            financials = fetch_financials(ticker)
            score, reasons = evaluate_stock(financials)
            price_eval, good_price = evaluate_price_target(financials["price"], target_price)
            price_history = get_price_history(ticker)

            # Basic Info
            st.subheader(f"📊 {financials['name']} ({ticker})")
            st.write(f"Sector: **{financials['sector']}**, Industry: **{financials['industry']}**")

            # Price Info
            if financials['price']:
                st.metric("Current Price", f"${financials['price']:.2f}")
            st.metric("Target Price", f"${target_price:.2f}")
            st.info(price_eval)

            # Price Chart
            st.subheader("📈 Price History (1 Year)")
            st.line_chart(price_history['Close'])

            # Score & Recommendation
            st.subheader("📌 Score & Recommendation")
            st.write(f"**Score:** {score}/100")
            st.success(get_recommendation(score))

            # Reasons
            st.subheader("📋 Reasons")
            for r in reasons:
                st.write(f"- {r}")

            # Key Metrics
            st.subheader("🔎 Key Metrics")
            metrics = [
                ("EPS", financials['eps'], 0),
                ("ROE", financials['return_on_equity'], 0.10),
                ("Revenue Growth", financials['revenue_growth'], 0.10),
                ("Debt/Equity", financials['debt_to_equity'], 1, False),
                ("P/E Ratio", financials['pe_ratio'], 20, False),
                ("Dividend Yield", financials['dividend_yield'], 0.02),
                ("PEG Ratio", financials['peg_ratio'], 1, False),
                ("Forward P/E", financials['forward_pe'], 20, False)
            ]
            for m in metrics:
                label, val, thresh = m[0], m[1], m[2]
                higher_is_better = m[3] if len(m) > 3 else True
                st.markdown(format_metric(label, val, thresh, higher_is_better))

            st.caption(f"⏳ Holding for: {hold_months} month(s)")

            # Save Analysis
            st.subheader("📁 Download Analysis")
            result = {
                "ticker": ticker,
                "score": score,
                "price": financials["price"],
                "target_price": target_price,
                "recommendation": get_recommendation(score).strip("✅🟢🟡❌ "),
                "date": datetime.date.today().isoformat()
            }
            st.download_button("Download Result (JSON)", json.dumps(result, indent=2), file_name=f"{ticker}_analysis.json")

        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
        