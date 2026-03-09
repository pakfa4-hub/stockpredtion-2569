import streamlit as st
import requests
import json
import time

# ── Config ────────────────────────────────────────────────────────────────
FINNHUB_KEY = 'd6nbcn1r01qm6a8c9et0d6nbcn1r01qm6a8c9etg'
GEMINI_KEY = st.secrets.get('GEMINI_KEY', '')

CRYPTO = {
    'BTC':'bitcoin','ETH':'ethereum','SOL':'solana','XRP':'ripple',
    'BNB':'binancecoin','ADA':'cardano','DOGE':'dogecoin','AVAX':'avalanche-2',
    'DOT':'polkadot','LINK':'chainlink','LTC':'litecoin','ATOM':'cosmos',
    'NEAR':'near','OP':'optimism','ARB':'arbitrum'
}

BINANCE_CRYPTO = set(['BTC','ETH','SOL','XRP','BNB','ADA','DOGE','AVAX',
    'DOT','LINK','LTC','ATOM','NEAR','OP','ARB','SUI','APT','PEPE'])

st.set_page_config(page_title="Trading Dashboard", page_icon="📊", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Sarabun:wght@300;400;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
.main { background: #060910; }
.stApp { background: #060910; color: #c9d1d9; }

.card {
    background: #0d1117; border: 1px solid #1c2333;
    border-radius: 10px; padding: 16px 18px; margin-bottom: 12px;
}
.card-label { font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #4a5568; margin-bottom: 8px; font-weight: 600; }
.card-value { font-family: 'Share Tech Mono', monospace; font-size: 22px; font-weight: 700; color: #fff; }
.card-sub { font-size: 12px; color: #4a5568; margin-top: 4px; }

.signal-buy  { background: rgba(0,230,118,.05); border: 2px solid #00e676; border-radius: 10px; padding: 20px; }
.signal-sell { background: rgba(255,61,87,.05);  border: 2px solid #ff3d57; border-radius: 10px; padding: 20px; }
.signal-wait { background: rgba(255,215,64,.05); border: 2px solid #ffd740; border-radius: 10px; padding: 20px; }

.bull { color: #00e676; } .bear { color: #ff3d57; } .neutral { color: #ffd740; } .accent { color: #58a6ff; }

.price-box { text-align: right; }
.price-big { font-family: 'Share Tech Mono', monospace; font-size: 36px; color: #fff; font-weight: 700; }

.ema-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #1c2333; }
.badge-above { background: rgba(0,230,118,.15); color: #00e676; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
.badge-below { background: rgba(255,61,87,.15);  color: #ff3d57; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }

.sltp-box { background: rgba(255,255,255,.02); border: 1px solid #1c2333; border-radius: 8px; padding: 12px; text-align: center; }
.sltp-label { font-size: 10px; letter-spacing: 1px; color: #4a5568; margin-bottom: 6px; }
.sltp-val { font-family: 'Share Tech Mono', monospace; font-size: 18px; font-weight: 700; }
.sltp-pct { font-size: 11px; margin-top: 4px; }

.rec-box { background: rgba(255,255,255,.02); border: 1px solid #1c2333; border-radius: 8px; padding: 12px; }
.rec-label { font-size: 10px; letter-spacing: 1.5px; color: #4a5568; text-transform: uppercase; margin-bottom: 6px; }
.rec-val { font-size: 13px; color: #c9d1d9; line-height: 1.5; }

.src-badge-live { display: inline-block; background: rgba(0,230,118,.08); border: 1px solid rgba(0,230,118,.2); border-radius: 20px; padding: 3px 12px; font-size: 11px; color: #00e676; }
.src-badge-warn { display: inline-block; background: rgba(255,215,64,.08); border: 1px solid rgba(255,215,64,.2); border-radius: 20px; padding: 3px 12px; font-size: 11px; color: #ffd740; }

.stButton > button {
    background: #58a6ff; color: #000; border: none; border-radius: 8px;
    padding: 10px 28px; font-weight: 700; font-size: 15px; cursor: pointer;
    transition: opacity .2s; width: 100%;
}
.stButton > button:hover { opacity: .85; background: #58a6ff; color: #000; }
.stTextInput > div > div > input {
    background: #0d1117; border: 1px solid #1c2333; color: #fff;
    border-radius: 8px; font-family: 'Share Tech Mono', monospace;
    font-size: 18px; letter-spacing: 2px; text-transform: uppercase;
}
div[data-testid="stHorizontalBlock"] { gap: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Fetch Price ────────────────────────────────────────────────────────────
def fetch_price(ticker):
    ticker = ticker.upper()

    if ticker in BINANCE_CRYPTO:
        # Binance
        try:
            sym = ticker + 'USDT'
            r1 = requests.get(f'https://api.binance.com/api/v3/ticker/price?symbol={sym}', timeout=5)
            r2 = requests.get(f'https://api.binance.com/api/v3/ticker/24hr?symbol={sym}', timeout=5)
            if r1.ok and r2.ok:
                price = float(r1.json()['price'])
                change = float(r2.json().get('priceChangePercent', 0))
                return {'price': price, 'change': change, 'source': 'Binance (real-time)', 'ok': True}
        except: pass
        # CoinGecko fallback
        cg_id = CRYPTO.get(ticker)
        if cg_id:
            try:
                r = requests.get(f'https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd&include_24hr_change=true', timeout=5)
                if r.ok:
                    j = r.json()
                    if j.get(cg_id, {}).get('usd'):
                        return {'price': j[cg_id]['usd'], 'change': j[cg_id].get('usd_24h_change', 0), 'source': 'CoinGecko', 'ok': True}
            except: pass

    else:
        # Finnhub
        try:
            r = requests.get(f'https://finnhub.io/api/v1/quote?symbol={ticker}&token={FINNHUB_KEY}', timeout=5)
            if r.ok:
                j = r.json()
                if j.get('c') and j['c'] != 0:
                    price = j['c']
                    prev = j.get('pc', price)
                    change = ((price - prev) / prev * 100) if prev else 0
                    return {'price': price, 'change': change, 'source': 'Finnhub (real-time)', 'ok': True}
        except: pass
        # Yahoo Finance fallback
        try:
            r = requests.get(
                f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d',
                headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            if r.ok:
                meta = r.json()['chart']['result'][0]['meta']
                price = meta['regularMarketPrice']
                prev = meta.get('chartPreviousClose', meta.get('previousClose', price))
                change = ((price - prev) / prev * 100) if prev else 0
                return {'price': price, 'change': change, 'source': 'Yahoo Finance', 'ok': True}
        except: pass

    return {'price': 0, 'change': 0, 'source': 'ดึงราคาไม่ได้', 'ok': False}

# ── AI Analyze ────────────────────────────────────────────────────────────
def ai_analyze(ticker, price_data):
    price_ctx = (
        f"ราคาปัจจุบัน (จาก {price_data['source']}): ${price_data['price']:.4f}, เปลี่ยน 24h: {price_data['change']:.2f}%"
        if price_data['ok']
        else "ดึงราคาไม่ได้ — ประมาณจากความรู้ล่าสุด"
    )

    prompt = f"""วิเคราะห์ "{ticker}" กลยุทธ์ EMA Multi-Timeframe (Monthly=Trend, Weekly=Entry, Daily=Confirm)
{price_ctx}
ตอบ JSON เท่านั้น ห้ามมีข้อความอื่น:
{{"ticker":"","fullName":"","exchange":"","signal":"buy|wait|sell","signalTitle":"ภาษาไทย","signalDesc":"1-2 ประโยค",
"trendMonthly":"up|down|side","trendWeekly":"up|down|side","trendDaily":"up|down|side",
"ema20":0,"ema50":0,"ema100":0,"ema200":0,"atr":0,"atrPct":0,
"entryZone":"","sl":0,"slPct":0,"tp1":0,"tp1Pct":0,"tp2":"",
"recStatus":"","recEntry":"","recExit":"","recRR":""}}"""

    r = requests.post(
        f'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-8b:generateContent?key={GEMINI_KEY}',
        headers={'Content-Type': 'application/json'},
        json={'contents': [{'parts': [{'text': prompt}]}]},
        timeout=30
    )
    rd = r.json()
    if 'candidates' not in rd:
        raise Exception(f"API Error: {rd.get('error', {}).get('message', str(rd))}")
    txt = rd['candidates'][0]['content']['parts'][0]['text']
    txt = txt.replace('```json', '').replace('```', '').strip()
    return json.loads(txt)

# ── Helpers ───────────────────────────────────────────────────────────────
def fmt(n):
    if n is None: return '—'
    try:
        n = float(n)
        if n >= 10000: return f"{n:,.0f}"
        if n >= 100:   return f"{n:,.2f}"
        if n >= 1:     return f"{n:.3f}"
        return f"{n:.5f}"
    except: return '—'

def trend_bar(t):
    color = '#00e676' if t == 'up' else '#ff3d57' if t == 'down' else '#ffd740'
    width = 75 if t == 'up' else 65 if t == 'down' else 50
    label = 'UP' if t == 'up' else 'DOWN' if t == 'down' else 'SIDE'
    cls = 'bull' if t == 'up' else 'bear' if t == 'down' else 'neutral'
    return f"""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
      <span style="font-size:10px;color:#4a5568;width:55px">{''}</span>
      <div style="flex:1;height:6px;border-radius:3px;background:#1c2333">
        <div style="width:{width}%;height:100%;border-radius:3px;background:{color}"></div>
      </div>
      <span class="{cls}" style="font-size:10px;font-weight:700;width:40px;text-align:right">{label}</span>
    </div>"""

# ── UI ────────────────────────────────────────────────────────────────────
st.markdown('<h1 style="font-family:Share Tech Mono,monospace;color:#fff;font-size:28px;margin-bottom:4px">📊 Trading Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#4a5568;font-size:12px;margin-bottom:20px">EMA Multi-Timeframe Strategy · AI Analysis · Real-time Price</p>', unsafe_allow_html=True)

# Search
col_input, col_btn = st.columns([5, 1])
with col_input:
    ticker_input = st.text_input('', placeholder='พิมพ์ชื่อหุ้น US หรือคริปโต เช่น AAPL, BTC, NVDA...', label_visibility='collapsed', key='ticker')
with col_btn:
    analyze_btn = st.button('🔍 วิเคราะห์')

# Quick picks
st.markdown("""
<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;margin-top:-8px">
  <span style="font-size:10px;color:#4a5568;align-self:center">🇺🇸</span>
""" + ''.join([f'<span style="background:#0d1117;border:1px solid #1c2333;border-radius:6px;padding:4px 10px;color:#4a5568;font-family:Share Tech Mono,monospace;font-size:12px">{t}</span>' for t in ['SPY','AAPL','NVDA','TSLA','MSFT','AMZN']]) +
'<span style="color:#1c2333">|</span><span style="font-size:10px;color:#4a5568;align-self:center">₿</span>' +
''.join([f'<span style="background:#0d1117;border:1px solid #1c2333;border-radius:6px;padding:4px 10px;color:#4a5568;font-family:Share Tech Mono,monospace;font-size:12px">{t}</span>' for t in ['BTC','ETH','SOL','XRP','BNB']]) +
'</div>', unsafe_allow_html=True)

# Analyze
if analyze_btn and ticker_input:
    ticker = ticker_input.strip().upper()

    with st.spinner(f'กำลังดึงราคา {ticker}...'):
        pd_data = fetch_price(ticker)

    with st.spinner(f'AI วิเคราะห์ {ticker}...'):
        try:
            d = ai_analyze(ticker, pd_data)
        except Exception as e:
            st.error(f'AI Error: {e}')
            st.stop()

    # Merge price
    if pd_data['ok']:
        d['currentPrice'] = pd_data['price']
        d['priceChange'] = pd_data['change']
        d['priceSource'] = pd_data['source']
        d['priceReal'] = True
    else:
        d['currentPrice'] = d.get('currentPrice', 0)
        d['priceChange'] = 0
        d['priceSource'] = 'AI ประมาณ'
        d['priceReal'] = False

    p = float(d.get('currentPrice') or 0)
    chg = float(d.get('priceChange') or 0)
    sig = d.get('signal', 'wait')

    # Source badge
    if d['priceReal']:
        st.markdown(f'<span class="src-badge-live">● ราคาจริงจาก {d["priceSource"]}</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="src-badge-warn">⚠️ {d["priceSource"]}</span>', unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # Header
    col_h1, col_h2 = st.columns([3, 2])
    with col_h1:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-family:Share Tech Mono,monospace;font-size:32px;font-weight:700;color:#fff">{d.get('ticker','—')}</span>
          <span style="font-size:11px;color:#4a5568;background:#0d1117;padding:3px 8px;border:1px solid #1c2333;border-radius:4px">{d.get('fullName','—')} · {d.get('exchange','—')}</span>
        </div>""", unsafe_allow_html=True)
    with col_h2:
        chg_color = '#00e676' if chg >= 0 else '#ff3d57'
        chg_arrow = '▲' if chg >= 0 else '▼'
        st.markdown(f"""
        <div class="price-box">
          <div class="price-big">${fmt(p)}</div>
          <div style="color:{chg_color};font-size:13px">{chg_arrow} {abs(chg):.2f}% (24h)</div>
          <div style="font-size:10px;color:{'#00e676' if d['priceReal'] else '#4a5568'}">● {'ราคาจริง' if d['priceReal'] else 'AI ประมาณ'}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown('<hr style="border-color:#1c2333;margin:16px 0">', unsafe_allow_html=True)

    # Signal
    sig_class = f'signal-{sig}'
    sig_color = '#00e676' if sig == 'buy' else '#ff3d57' if sig == 'sell' else '#ffd740'
    sig_label = 'ซื้อ' if sig == 'buy' else 'ขาย' if sig == 'sell' else 'รอ'
    sig_emoji = '🟢' if sig == 'buy' else '🔴' if sig == 'sell' else '⏳'
    st.markdown(f"""
    <div class="{sig_class}" style="margin-bottom:16px;display:flex;align-items:center;gap:20px">
      <div style="width:80px;height:80px;border-radius:50%;border:2px solid {sig_color};display:flex;align-items:center;justify-content:center;flex-shrink:0;color:{sig_color};font-size:14px;font-weight:700;background:rgba(0,0,0,.3)">
        {sig_label}
      </div>
      <div>
        <div style="font-size:18px;font-weight:700;color:#fff;margin-bottom:6px">{sig_emoji} {d.get('signalTitle','')}</div>
        <div style="font-size:13px;color:#4a5568;line-height:1.6">{d.get('signalDesc','')}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    # Row 1: Trend, EMA, ATR
    c1, c2, c3 = st.columns(3)

    with c1:
        tm = d.get('trendMonthly','side')
        tw = d.get('trendWeekly','side')
        td = d.get('trendDaily','side')
        def trow(label, t):
            color = '#00e676' if t=='up' else '#ff3d57' if t=='down' else '#ffd740'
            w = 75 if t=='up' else 65 if t=='down' else 50
            lbl = 'UP' if t=='up' else 'DOWN' if t=='down' else 'SIDE'
            return f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
              <span style="font-size:10px;color:#4a5568;width:55px">{label}</span>
              <div style="flex:1;height:6px;border-radius:3px;background:#1c2333">
                <div style="width:{w}%;height:100%;border-radius:3px;background:{color}"></div>
              </div>
              <span style="font-size:10px;font-weight:700;color:{color};width:40px;text-align:right">{lbl}</span>
            </div>"""
        st.markdown(f"""
        <div class="card">
          <div class="card-label">Trend ทุก Timeframe</div>
          {trow('Monthly', tm)}{trow('Weekly', tw)}{trow('Daily', td)}
        </div>""", unsafe_allow_html=True)

    with c2:
        def erow(label, val):
            badge = '<span class="badge-above">เหนือ</span>' if p >= float(val or 0) else '<span class="badge-below">ต่ำกว่า</span>'
            return f"""<div class="ema-row">
              <span style="font-size:12px;color:#4a5568">{label}</span>
              <span style="font-family:Share Tech Mono,monospace;font-size:13px;color:#fff">{fmt(val)}</span>
              {badge}
            </div>"""
        st.markdown(f"""
        <div class="card">
          <div class="card-label">EMA Monthly (AI ประมาณ)</div>
          {erow('EMA 20', d.get('ema20'))}{erow('EMA 50', d.get('ema50'))}
          {erow('EMA 100', d.get('ema100'))}{erow('EMA 200', d.get('ema200'))}
        </div>""", unsafe_allow_html=True)

    with c3:
        atr_pct = float(d.get('atrPct') or 0)
        atr_w = min(atr_pct * 5, 95)
        st.markdown(f"""
        <div class="card">
          <div class="card-label">ATR Monthly (AI ประมาณ)</div>
          <div class="card-value">{fmt(d.get('atr'))}</div>
          <div class="card-sub">~{atr_pct:.1f}% ของราคา</div>
          <div style="margin-top:10px;background:#1c2333;border-radius:4px;height:8px;overflow:hidden">
            <div style="width:{atr_w}%;height:100%;background:linear-gradient(90deg,#00e676,#ffd740);border-radius:4px"></div>
          </div>
          <div style="display:flex;justify-content:space-between;margin-top:5px;font-size:10px;color:#4a5568">
            <span>ต่ำ</span><span>ปานกลาง</span><span>สูง</span>
          </div>
        </div>""", unsafe_allow_html=True)

    # Row 2: SL/TP
    st.markdown('<div class="card"><div class="card-label">จุด Entry / SL / TP</div>', unsafe_allow_html=True)
    s1,s2,s3,s4 = st.columns(4)
    with s1:
        st.markdown(f'<div class="sltp-box"><div class="sltp-label">ENTRY ZONE</div><div class="sltp-val accent">{d.get("entryZone","—")}</div><div class="sltp-pct" style="color:#4a5568">แนวรับ / EMA</div></div>', unsafe_allow_html=True)
    with s2:
        st.markdown(f'<div class="sltp-box"><div class="sltp-label">STOP LOSS</div><div class="sltp-val bear">{fmt(d.get("sl"))}</div><div class="sltp-pct bear">≈ -{abs(float(d.get("slPct") or 0)):.1f}%</div></div>', unsafe_allow_html=True)
    with s3:
        st.markdown(f'<div class="sltp-box"><div class="sltp-label">TP1</div><div class="sltp-val bull">{fmt(d.get("tp1"))}</div><div class="sltp-pct bull">+{float(d.get("tp1Pct") or 0):.1f}%</div></div>', unsafe_allow_html=True)
    with s4:
        st.markdown(f'<div class="sltp-box"><div class="sltp-label">TP2 (ถือยาว)</div><div class="sltp-val" style="color:#69e0a5">{d.get("tp2","—")}</div><div class="sltp-pct" style="color:#4a5568">ตาม EMA 50</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Row 3: Recommendations
    st.markdown('<div class="card"><div class="card-label">📋 คำแนะนำ</div>', unsafe_allow_html=True)
    r1,r2,r3,r4,r5 = st.columns(5)
    recs = [
        ('สถานะ', f'<span style="color:#ffd740;font-weight:700">{d.get("recStatus","—")}</span>'),
        ('เงื่อนไขเข้าซื้อ', d.get('recEntry','—')),
        ('ออกเมื่อ', d.get('recExit','—')),
        ('Risk/Reward', d.get('recRR','—')),
        ('Position Size', 'Risk <span style="color:#ffd740;font-weight:700">1% ของพอร์ต</span> ÷ ระยะ SL'),
    ]
    for col, (label, val) in zip([r1,r2,r3,r4,r5], recs):
        with col:
            st.markdown(f'<div class="rec-box"><div class="rec-label">{label}</div><div class="rec-val">{val}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f'<p style="font-size:11px;color:#4a5568;margin-top:16px">⚠️ เพื่อการศึกษาเท่านั้น · ไม่ใช่คำแนะนำลงทุน · EMA/ATR/SL/TP ประมาณโดย AI · {time.strftime("%d/%m/%Y %H:%M")}</p>', unsafe_allow_html=True)

elif not ticker_input:
    st.markdown("""
    <div style="text-align:center;padding:60px 20px;color:#4a5568">
      <div style="font-size:48px;margin-bottom:16px">📊</div>
      <div style="font-size:16px">พิมพ์ชื่อหุ้น US หรือคริปโตด้านบน</div>
      <div style="font-size:13px;margin-top:8px">
        <span style="color:#00e676">คริปโต</span> — Binance real-time &nbsp;·&nbsp;
        <span style="color:#58a6ff">หุ้น US</span> — Finnhub / Yahoo Finance
      </div>
    </div>""", unsafe_allow_html=True)
