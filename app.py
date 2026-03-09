import streamlit as st
import requests
import pandas as pd
import numpy as np

# ---------------- CONFIG ----------------

FINNHUB_KEY = "d6nbcn1r01qm6a8c9et0d6nbcn1r01qm6a8c9etg"

BINANCE_CRYPTO = {
    "BTC","ETH","SOL","XRP","BNB","ADA","DOGE","AVAX"
}

st.set_page_config(
    page_title="Trading Dashboard PRO",
    page_icon="📊",
    layout="wide"
)

# ---------------- STYLE ----------------

st.markdown("""
<style>

.main{
background:#060910;
}

.price{
font-size:42px;
font-weight:700;
}

.buy{border:2px solid #00e676;padding:20px;border-radius:10px}
.sell{border:2px solid #ff3d57;padding:20px;border-radius:10px}
.wait{border:2px solid #ffd740;padding:20px;border-radius:10px}

</style>
""", unsafe_allow_html=True)

# ---------------- PRICE ----------------

def fetch_price(ticker):

    ticker = ticker.upper()

    # CRYPTO
    if ticker in BINANCE_CRYPTO:

        try:

            sym = ticker + "USDT"

            r = requests.get(
                f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}",
                timeout=5
            )

            j = r.json()

            return {
                "price": float(j["lastPrice"]),
                "change": float(j["priceChangePercent"]),
                "source": "Binance",
                "ok": True
            }

        except:
            pass

    # STOCK
    try:

        r = requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}",
            timeout=5
        )

        j = r.json()

        price = j["c"]
        prev = j["pc"]

        chg = ((price - prev) / prev) * 100

        return {
            "price": price,
            "change": chg,
            "source": "Finnhub",
            "ok": True
        }

    except:
        pass

    # Yahoo fallback
    try:

        r = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1mo&interval=1d",
            headers={"User-Agent":"Mozilla"}
        )

        meta = r.json()["chart"]["result"][0]["meta"]

        price = meta["regularMarketPrice"]
        prev = meta["chartPreviousClose"]

        chg = ((price - prev) / prev) * 100

        return {
            "price": price,
            "change": chg,
            "source": "Yahoo",
            "ok": True
        }

    except:
        pass

    return {
        "price": 0,
        "change": 0,
        "source": "none",
        "ok": False
    }

# ---------------- CANDLES ----------------

def fetch_candles(ticker):

    ticker = ticker.upper()

    # CRYPTO
    if ticker in BINANCE_CRYPTO:

        try:

            sym = ticker + "USDT"

            r = requests.get(
                f"https://api.binance.com/api/v3/klines?symbol={sym}&interval=1h&limit=200"
            )

            data = r.json()

            df = pd.DataFrame(data)

            df = df[[0,1,2,3,4,5]]

            df.columns = ["time","open","high","low","close","volume"]

            df["close"] = df["close"].astype(float)

            return df

        except:
            return None

    # STOCK
    try:

        r = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=6mo&interval=1d",
            headers={"User-Agent":"Mozilla"}
        )

        j = r.json()["chart"]["result"][0]

        df = pd.DataFrame()

        df["close"] = j["indicators"]["quote"][0]["close"]

        return df

    except:
        return None

# ---------------- INDICATORS ----------------

def add_indicators(df):

    df["ema20"] = df["close"].ewm(span=20).mean()
    df["ema50"] = df["close"].ewm(span=50).mean()
    df["ema100"] = df["close"].ewm(span=100).mean()
    df["ema200"] = df["close"].ewm(span=200).mean()

    df["tr"] = abs(df["close"].diff())
    df["atr"] = df["tr"].rolling(14).mean()

    return df

# ---------------- ANALYSIS ----------------

def analyze(df):

    price = df["close"].iloc[-1]

    ema20 = df["ema20"].iloc[-1]
    ema50 = df["ema50"].iloc[-1]
    ema100 = df["ema100"].iloc[-1]
    ema200 = df["ema200"].iloc[-1]

    atr = df["atr"].iloc[-1]

    signal = "wait"

    if price > ema20 > ema50:
        signal = "buy"

    if price < ema20 < ema50:
        signal = "sell"

    entry = ema20
    sl = entry - (atr * 2)
    tp = entry + (atr * 4)

    return {
        "signal": signal,
        "ema20": ema20,
        "ema50": ema50,
        "ema100": ema100,
        "ema200": ema200,
        "atr": atr,
        "entry": entry,
        "sl": sl,
        "tp": tp
    }

# ---------------- UI ----------------

st.title("📊 Trading Dashboard PRO")

colA, colB = st.columns([4,1])

with colA:
    ticker = st.text_input("Ticker", "TSLA")

with colB:
    run = st.button("Analyze")

if run:

    price_data = fetch_price(ticker)

    df = fetch_candles(ticker)

    if df is None:
        st.error("No data")
        st.stop()

    df = add_indicators(df)

    analysis = analyze(df)

    price = price_data["price"]
    chg = price_data["change"]

    col1, col2 = st.columns([3,1])

    with col1:
        st.subheader(ticker)

    with col2:
        st.markdown(
            f"<div class='price'>${price:.2f}</div>",
            unsafe_allow_html=True
        )
        st.write(f"{chg:.2f}%")

    sig = analysis["signal"]

    box = "wait"
    if sig == "buy":
        box = "buy"
    if sig == "sell":
        box = "sell"

    st.markdown(
        f"<div class='{box}'><b>{sig.upper()}</b></div>",
        unsafe_allow_html=True
    )

    st.subheader("Chart")

    chart = df[["close","ema20","ema50"]]

    st.line_chart(chart)

    st.subheader("EMA")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("EMA20", f"{analysis['ema20']:.2f}")
    c2.metric("EMA50", f"{analysis['ema50']:.2f}")
    c3.metric("EMA100", f"{analysis['ema100']:.2f}")
    c4.metric("EMA200", f"{analysis['ema200']:.2f}")

    st.subheader("Trade Setup")

    s1, s2, s3 = st.columns(3)

    s1.metric("Entry", f"{analysis['entry']:.2f}")
    s2.metric("Stop Loss", f"{analysis['sl']:.2f}")
    s3.metric("Take Profit", f"{analysis['tp']:.2f}")

    st.subheader("ATR")

    st.metric("ATR", f"{analysis['atr']:.2f}")

    st.caption("For education only")
