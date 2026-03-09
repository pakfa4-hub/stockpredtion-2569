import streamlit as st
import requests
import json
import time

# ---------------- CONFIG ----------------

FINNHUB_KEY = "d6nbcn1r01qm6a8c9et0d6nbcn1r01qm6a8c9etg"
GEMINI_KEY = ""   # ใส่ Gemini key ถ้ามี

CRYPTO = {
'BTC':'bitcoin','ETH':'ethereum','SOL':'solana','XRP':'ripple',
'BNB':'binancecoin','ADA':'cardano','DOGE':'dogecoin'
}

BINANCE_CRYPTO = set([
'BTC','ETH','SOL','XRP','BNB','ADA','DOGE'
])

st.set_page_config(
page_title="Trading Dashboard",
page_icon="📊",
layout="wide"
)

# ---------------- STYLE ----------------

st.markdown("""
<style>

.main {
background:#060910;
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

.buy{
border:2px solid #00e676;
padding:20px;
border-radius:10px;
}

.sell{
border:2px solid #ff3d57;
padding:20px;
border-radius:10px;
}

.wait{
border:2px solid #ffd740;
padding:20px;
border-radius:10px;
}

</style>
""", unsafe_allow_html=True)

# ---------------- PRICE FETCH ----------------

def fetch_price(ticker):

ticker=ticker.upper()

# CRYPTO
if ticker in BINANCE_CRYPTO:

try:

sym=ticker+"USDT"

r=requests.get(
f"https://api.binance.com/api/v3/ticker/24hr?symbol={sym}",
timeout=5
)

if r.ok:

j=r.json()

price=float(j["lastPrice"])
change=float(j["priceChangePercent"])

return {
"price":price,
"change":change,
"source":"Binance",
"ok":True
}

except:
pass


# STOCK
try:

r=requests.get(
f"https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}",
timeout=5
)

if r.ok:

j=r.json()

if j["c"]!=0:

price=j["c"]
prev=j["pc"]

change=((price-prev)/prev)*100

return {
"price":price,
"change":change,
"source":"Finnhub",
"ok":True
}

except:
pass


# Yahoo fallback
try:

r=requests.get(
f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d",
headers={"User-Agent":"Mozilla/5.0"},
timeout=5
)

if r.ok:

meta=r.json()["chart"]["result"][0]["meta"]

price=meta["regularMarketPrice"]
prev=meta["chartPreviousClose"]

change=((price-prev)/prev)*100

return {
"price":price,
"change":change,
"source":"Yahoo",
"ok":True
}

except:
pass


return {
"price":0,
"change":0,
"source":"none",
"ok":False
}

# ---------------- AI ANALYSIS ----------------

def ai_analyze(ticker,price_data):

price=price_data["price"]

def fallback():

return {
"ticker":ticker,
"fullName":ticker,
"exchange":"Market",

"signal":"wait",
"signalTitle":"รอจังหวะ",
"signalDesc":"AI quota หมด ใช้วิเคราะห์พื้นฐาน",

"trendMonthly":"side",
"trendWeekly":"side",
"trendDaily":"side",

"ema20":price*0.97,
"ema50":price*0.94,
"ema100":price*0.90,
"ema200":price*0.85,

"atr":price*0.04,
"atrPct":4,

"entryZone":f"{price*0.95:.2f}-{price*0.97:.2f}",

"sl":price*0.90,
"slPct":-10,

"tp1":price*1.10,
"tp1Pct":10,

"tp2":"ถือยาว",

"recStatus":"รอ",
"recEntry":"รอย่อ",
"recExit":"หลุด EMA",
"recRR":"1:2"
}

if GEMINI_KEY=="":

return fallback()

try:

prompt=f"Analyze {ticker} price {price}"

r=requests.post(
f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}",
headers={"Content-Type":"application/json"},
json={
"contents":[
{"parts":[{"text":prompt}]}
]
},
timeout=20
)

rd=r.json()

if "candidates" not in rd:

return fallback()

txt=rd["candidates"][0]["content"]["parts"][0]["text"]

return json.loads(txt)

except:

return fallback()

# ---------------- FORMAT ----------------

def fmt(n):

try:

n=float(n)

if n>=10000:
return f"{n:,.0f}"

if n>=100:
return f"{n:,.2f}"

if n>=1:
return f"{n:.3f}"

return f"{n:.5f}"

except:
return "-"

# ---------------- UI ----------------

st.title("📊 Trading Dashboard")

ticker=st.text_input(
"Ticker",
value="TSLA"
)

if st.button("Analyze"):

with st.spinner("Fetching price..."):

price_data=fetch_price(ticker)

with st.spinner("Analyzing..."):

data=ai_analyze(ticker,price_data)

price=price_data["price"]
chg=price_data["change"]

col1,col2=st.columns([3,1])

with col1:

st.subheader(data["ticker"])

with col2:

color="green" if chg>=0 else "red"

st.markdown(
f"<div class='price'>${fmt(price)}</div>",
unsafe_allow_html=True
)

st.write(f"{chg:.2f}%")

sig=data["signal"]

box="buy" if sig=="buy" else "sell" if sig=="sell" else "wait"

st.markdown(
f"<div class='{box}'><b>{data['signalTitle']}</b><br>{data['signalDesc']}</div>",
unsafe_allow_html=True
)

st.write("### Trend")

c1,c2,c3=st.columns(3)

c1.metric("Monthly",data["trendMonthly"])
c2.metric("Weekly",data["trendWeekly"])
c3.metric("Daily",data["trendDaily"])

st.write("### EMA")

e1,e2,e3,e4=st.columns(4)

e1.metric("EMA20",fmt(data["ema20"]))
e2.metric("EMA50",fmt(data["ema50"]))
e3.metric("EMA100",fmt(data["ema100"]))
e4.metric("EMA200",fmt(data["ema200"]))

st.write("### Entry / SL / TP")

s1,s2,s3=st.columns(3)

s1.metric("Entry",data["entryZone"])
s2.metric("Stop Loss",fmt(data["sl"]))
s3.metric("Take Profit",fmt(data["tp1"]))

st.write("### Recommendation")

r1,r2,r3=st.columns(3)

r1.write(data["recStatus"])
r2.write(data["recEntry"])
r3.write(data["recRR"])

st.caption("เพื่อการศึกษาเท่านั้น")
