import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import google.generativeai as genai

# ---------------------------
# CONFIG
# ---------------------------

st.set_page_config(
    page_title="Trading Dashboard",
    layout="wide"
)

# ---------------------------
# CSS STYLE
# ---------------------------

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Sarabun:wght@300;400;700&display=swap');

html, body, [class*="css"]  {
    font-family: 'Sarabun', sans-serif;
    background-color:#0d1117;
}

h1{
    font-family: 'Share Tech Mono', monospace;
    color:#58a6ff;
}

.subtitle{
    color:#8b949e;
    margin-bottom:20px;
}

.stTextInput input{
    background:#0d1117;
    border:1px solid #1c2333;
    color:white;
    border-radius:8px;
    padding:10px;
    font-family:'Share Tech Mono', monospace;
    letter-spacing:2px;
}

.stButton button{
    background:#58a6ff;
    color:white;
    border-radius:8px;
    padding:10px 18px;
    font-weight:700;
}

.card{
    background:#161b22;
    padding:20px;
    border-radius:12px;
    border:1px solid #30363d;
}

.metric{
    font-size:28px;
    font-weight:700;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------
# HEADER
# ---------------------------

st.markdown("# 📊 Trading Dashboard")

st.markdown(
'<div class="subtitle">EMA Multi-Timeframe Strategy · AI Analysis · Real-time Price</div>',
unsafe_allow_html=True
)

# ---------------------------
# INPUT
# ---------------------------

col1,col2 = st.columns([4,1])

with col1:
    ticker = st.text_input("",value="TSLA")

with col2:
    analyze = st.button("🔎 Analyze")

# Quick picks
st.caption("SPY  AAPL  NVDA  TSLA  MSFT  AMZN   |   BTC-USD  ETH-USD")

# ---------------------------
# DATA
# ---------------------------

@st.cache_data
def load_data(ticker):

    df = yf.download(ticker,period="6mo",interval="1d")

    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()
    df["EMA200"] = df["Close"].ewm(span=200).mean()

    return df

if analyze:

    try:

        df = load_data(ticker)

        if df.empty:
            st.error("Ticker not found")
            st.stop()

        price = df["Close"].iloc[-1]
        change = df["Close"].pct_change().iloc[-1]*100

        # ---------------------------
        # METRICS
        # ---------------------------

        col1,col2,col3 = st.columns(3)

        with col1:
            st.metric("Price",f"${price:,.2f}")

        with col2:
            st.metric("Daily Change",f"{change:.2f}%")

        with col3:
            st.metric("Volume",f"{df['Volume'].iloc[-1]:,.0f}")

        # ---------------------------
        # CHART
        # ---------------------------

        fig = go.Figure()

        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Price"
        ))

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["EMA20"],
            line=dict(width=1),
            name="EMA20"
        ))

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["EMA50"],
            line=dict(width=1),
            name="EMA50"
        ))

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df["EMA200"],
            line=dict(width=1),
            name="EMA200"
        ))

        fig.update_layout(
            template="plotly_dark",
            height=600
        )

        st.plotly_chart(fig,use_container_width=True)

        # ---------------------------
        # STRATEGY
        # ---------------------------

        ema20 = df["EMA20"].iloc[-1]
        ema50 = df["EMA50"].iloc[-1]
        ema200 = df["EMA200"].iloc[-1]

        if ema20 > ema50 > ema200:
            signal = "📈 Strong Uptrend"
        elif ema20 < ema50 < ema200:
            signal = "📉 Downtrend"
        else:
            signal = "⚠️ Sideway"

        st.subheader("Strategy Signal")
        st.success(signal)

        # ---------------------------
        # AI ANALYSIS
        # ---------------------------

        st.subheader("🤖 AI Analysis")

        try:

            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

            model = genai.GenerativeModel("gemini-1.5-flash")

            prompt = f"""
            Analyze this stock:

            Ticker: {ticker}
            Price: {price}

            EMA20: {ema20}
            EMA50: {ema50}
            EMA200: {ema200}

            Give short trading insight.
            """

            response = model.generate_content(prompt)

            st.write(response.text)

        except:
            st.warning("AI analysis unavailable")

    except Exception as e:

        st.error(f"Error: {e}")
