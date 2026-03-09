import streamlit as st
import requests
import pandas as pd

FINNHUB_KEY="d6nbcn1r01qm6a8c9et0d6nbcn1r01qm6a8c9etg"

BINANCE_CRYPTO={"BTC","ETH","SOL","XRP","BNB","ADA","DOGE"}

st.set_page_config(page_title="Trading Dashboard",layout="wide")

# ---------- CSS ----------

st.markdown("""
<style>

body{
background:#060910;
color:white;
}

.card{
background:#0d1117;
border:1px solid #1c2333;
border-radius:10px;
padding:16px;
margin-bottom:12px;
}

.price{
font-size:36px;
font-weight:700;
}

.buy{border:2px solid #00e676;padding:20px;border-radius:10px}
.sell{border:2px solid #ff3d57;padding:20px;border-radius:10px}
.wait{border:2px solid #ffd740;padding:20px;border-radius:10px}

</style>
""",unsafe_allow_html=True)

# ---------- PRICE ----------

def fetch_price(ticker):

    ticker=ticker.upper()

    if ticker in BINANCE_CRYPTO:

        try:

            sym=ticker+"USDT"

            r=requests.get(
                f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}"
            )

            j=r.json()

            return {
                "price":float(j["lastPrice"]),
                "change":float(j["priceChangePercent"]),
                "source":"Binance",
                "ok":True
            }

        except:
            pass

    try:

        r=requests.get(
            f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}"
        )

        j=r.json()

        price=j["c"]
        prev=j["pc"]

        chg=((price-prev)/prev)*100

        return{
            "price":price,
            "change":chg,
            "source":"Finnhub",
            "ok":True
        }

    except:
        pass

    return{"price":0,"change":0,"source":"none","ok":False}

# ---------- CANDLES ----------

def fetch_candles(ticker):

    ticker=ticker.upper()

    try:

        r=requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=6mo&interval=1d",
            headers={"User-Agent":"Mozilla"}
        )

        j=r.json()["chart"]["result"][0]

        df=pd.DataFrame()

        df["close"]=j["indicators"]["quote"][0]["close"]

        return df

    except:
        return None

# ---------- INDICATORS ----------

def indicators(df):

    df["ema20"]=df["close"].ewm(span=20).mean()
    df["ema50"]=df["close"].ewm(span=50).mean()
    df["ema100"]=df["close"].ewm(span=100).mean()
    df["ema200"]=df["close"].ewm(span=200).mean()

    df["tr"]=abs(df["close"].diff())
    df["atr"]=df["tr"].rolling(14).mean()

    return df

# ---------- ANALYSIS ----------

def analyze(df):

    price=df["close"].iloc[-1]

    ema20=df["ema20"].iloc[-1]
    ema50=df["ema50"].iloc[-1]

    atr=df["atr"].iloc[-1]

    signal="wait"

    if price>ema20>ema50:
        signal="buy"

    if price<ema20<ema50:
        signal="sell"

    entry=ema20
    sl=entry-(atr*2)
    tp=entry+(atr*4)

    return signal,ema20,ema50,atr,entry,sl,tp

# ---------- UI ----------

st.title("📊 Trading Dashboard")

col1,col2=st.columns([5,1])

with col1:
    ticker=st.text_input("Ticker","TSLA")

with col2:
    run=st.button("Analyze")

if run:

    price_data=fetch_price(ticker)

    df=fetch_candles(ticker)

    if df is None:
        st.error("No data")
        st.stop()

    df=indicators(df)

    signal,ema20,ema50,atr,entry,sl,tp=analyze(df)

    price=price_data["price"]
    chg=price_data["change"]

    c1,c2=st.columns([3,1])

    with c1:
        st.subheader(ticker)

    with c2:
        st.markdown(f"<div class='price'>${price:.2f}</div>",unsafe_allow_html=True)
        st.write(f"{chg:.2f}%")

    box="wait"

    if signal=="buy":
        box="buy"

    if signal=="sell":
        box="sell"

    st.markdown(f"<div class='{box}'><b>{signal.upper()}</b></div>",unsafe_allow_html=True)

    st.subheader("Chart")

    st.line_chart(df[["close","ema20","ema50"]])

    st.subheader("EMA")

    e1,e2=st.columns(2)

    e1.metric("EMA20",f"{ema20:.2f}")
    e2.metric("EMA50",f"{ema50:.2f}")

    st.subheader("Trade Setup")

    s1,s2,s3=st.columns(3)

    s1.metric("Entry",f"{entry:.2f}")
    s2.metric("Stop Loss",f"{sl:.2f}")
    s3.metric("Take Profit",f"{tp:.2f}")

    st.subheader("ATR")

    st.metric("ATR",f"{atr:.2f}")
