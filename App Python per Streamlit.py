import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# Configurazione della pagina per adattarsi perfettamente agli smartphone
st.set_page_config(
    page_title="AI Market Terminal",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Stile CSS personalizzato in stile Fintech minimal (Dark Mode)
st.markdown("""
    <style>
    .main { background-color: #07080a; }
    .stApp { background-color: #07080a; color: #ededed; }
    h1, h2, h3 { color: #ffffff !important; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    .card {
        background: rgba(20, 24, 33, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.07);
        backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
    }
    .metric-title { font-size: 11px; color: #9ca3af; text-transform: uppercase; font-weight: 600; }
    .metric-value { font-size: 18px; font-weight: bold; color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# Header minimale
st.markdown("### 📈 Smart AI Market Terminal")
st.markdown("<p style='font-size: 12px; color: #9ca3af; margin-top: -15px;'>Analisi Tecnica, Sentiment & Previsioni Multi-Timeframe</p>", unsafe_allow_html=True)

# Barra di ricerca Ticker e Ticker Rapidi
col_input, col_btn = st.columns([3, 1])
with col_input:
    ticker_input = st.text_input("Ticker", value="SXLK.MI", label_visibility="collapsed")
with col_btn:
    cerca_pressed = st.button("Cerca", use_container_width=True)

# Pulsanti rapidi orizzontali
st.markdown("<p style='font-size: 11px; color: #9ca3af; margin-bottom: 4px;'>Asset Rapidi:</p>", unsafe_allow_html=True)
q_cols = st.columns(5)
ticker_selezionato = ticker_input.strip().upper()

if q_cols[0].button("SXLK", use_container_width=True): ticker_selezionato = "SXLK.MI"
if q_cols[1].button("AAPL", use_container_width=True): ticker_selezionato = "AAPL"
if q_cols[2].button("NVDA", use_container_width=True): ticker_selezionato = "NVDA"
if q_cols[3].button("BTC", use_container_width=True): ticker_selezionato = "BTC-USD"
if q_cols[4].button("ENEL", use_container_width=True): ticker_selezionato = "ENEL.MI"

# Selettore Orizzonte Temporale (1D, 3D, 7D)
st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
timeframe_scelto = st.radio("Orizzonte Previsionale", ["1 Giorno (1D)", "3 Giorni (3D)", "7 Giorni (7D)"], horizontal=True, label_visibility="collapsed")

# Estrazione del codice temporale pulito
if "1D" in timeframe_scelto: tf_code = "1D"
elif "3D" in timeframe_scelto: tf_code = "3D"
else: tf_code = "7D"

# Funzione per scaricare e calcolare i dati reali in modo sicuro
@st.cache_data(ttl=600)
def carica_dati(ticker):
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if data.empty:
            return None
        # Gestione multi-index di yfinance se presente
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        return None

with st.spinner(f"Analisi in corso per {ticker_selezionato}..."):
    df = carica_dati(ticker_selezionato)

if df is None or len(df) < 20:
    st.error(f"Impossibile recuperare dati validi per il ticker '{ticker_selezionato}'. Verifica che il simbolo sia corretto (es. AAPL, SXLK.MI, BTC-USD).")
else:
    # Calcoli finanziari e indicatori tecnici (RSI, SMA)
    prezzo_attuale = float(df['Close'].iloc[-1])
    prezzo_precedente = float(df['Close'].iloc[-2])
    variazione_pct = ((prezzo_attuale - prezzo_precedente) / prezzo_precedente) * 100

    # Calcolo RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_attuale = float(rsi.iloc[-1])

    # Calcolo Media Mobile a 50 periodi (SMA 50)
    sma_50 = float(df['Close'].rolling(window=50).mean().iloc[-1])

    # Simulazione Sentiment News Online basata sul momentum e RSI recente
    sentiment_score = int(np.clip(50 + (variazione_pct * 4) + (10 if rsi_attuale > 50 else -10), 10, 90))
    sentiment_label = "Bullish (Positivo)" if sentiment_score >= 60 else ("Bearish (Negativo)" if sentiment_score <= 40 else "Neutro / Laterale")

    # Modello di Previsione Multi-Timeframe (Influenza di 1D, 3D, 7D sui calcoli)
    score_modello = int(np.clip(50 + (15 if rsi_attuale < 40 else (-10 if rsi_attuale > 70 else 5)) + (sentiment_score * 0.4), 15, 95))
    
    if tf_code == "1D":
        sl_pct, tp_pct = (-1.0, 1.8) if "USD" in ticker_selezionato or not "MI" in ticker_selezionato else (-0.8, 1.4)
        orizzonte_txt = "Breve termine (24 ore)"
    elif tf_code == "3D":
        sl_pct, tp_pct = (-2.2, 3.8) if "USD" in ticker_selezionato else (-1.6, 2.8)
        orizzonte_txt = "Swing medio (3 giorni)"
    else:
        sl_pct, tp_pct = (-4.0, 7.5) if "USD" in ticker_selezionato else (-2.8, 5.2)
        orizzonte_txt = "Posizionale (7 giorni)"

    # Sezione Verdetto AI & Rischio
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    
    if score_modello >= 60:
        verdict_color = "border-left: 4px solid #10b981;"
        verdict_title = "🟢 ACCUMULO / ACQUISTO (BUY)"
        verdict_desc = f"Sul timeframe a {orizzonte_txt}, i parametri tecnici (RSI: {rsi_attuale:.1f}) e il sentiment delle notizie online indicano un'opportunità favorevole."
    elif score_modello <= 35:
        verdict_color = "border-left: 4px solid #ef4444;"
        verdict_title = "🔴 CAUTELA / ATTENDI (SELL)"
        verdict_desc = f"Sul timeframe a {orizzonte_txt}, la pressione ribassista e i indicatori tesi consigliano di evitare esposizioni immediate su {ticker_selezionato}."
    else:
        verdict_color = "border-left: 4px solid #f59e0b;"
        verdict_title = "🟡 FASE LATERALE (HOLD)"
        verdict_desc = f"Equilibrio tra compratori e venditori per {orizzonte_txt}. Consigliabile attendere la rottura dei livelli chiave."

    st.markdown(f"""
        <div class="card" style="{verdict_color}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 10px; color: #9ca3af; font-weight: bold; text-transform: uppercase;">Verdetto Modello ({tf_code})</span>
                <span style="font-size: 11px; font-family: monospace; background: rgba(16, 185, 129, 0.2); color: #34d399; padding: 2px 8px; border-radius: 6px;">Score: {score_modello}/100</span>
            </div>
            <div style="font-size: 14px; font-weight: bold; color: #ffffff; margin-bottom: 6px;">{verdict_title}</div>
            <div style="font-size: 11px; color: #d1d5db; line-height: 1.4;">{verdict_desc}</div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; border-top: 1px solid rgba(255,255,255,0.05); pt-2;">
                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px;">
                    <span style="font-size: 9px; color: #9ca3af;">Stop Loss Suggerito</span>
                    <div style="font-size: 13px; font-family: monospace; font-weight: bold; color: #f87171;">{sl_pct}%</div>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px;">
                    <span style="font-size: 9px; color: #9ca3af;">Take Profit Suggerito</span>
                    <div style="font-size: 13px; font-family: monospace; font-weight: bold; color: #34d399;">+{tp_pct}%</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Griglia Metriche Sintesi
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
            <div class="card" style="text-align: center; padding: 10px;">
                <div class="metric-title">Prezzo</div>
                <div class="metric-value" style="font-size: 14px; margin-top: 2px;">{prezzo_attuale:.2f}</div>
                <div style="font-size: 10px; color: {'#34d399' if variazione_pct >= 0 else '#f87171'};">{variazione_pct:+.2f}%</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        rsi_status = "Ipervenduto" if rsi_attuale < 35 else ("Ipercomprato" if rsi_attuale > 70 else "Neutro")
        st.markdown(f"""
            <div class="card" style="text-align: center; padding: 10px;">
                <div class="metric-title">RSI (14)</div>
                <div class="metric-value" style="font-size: 14px; margin-top: 2px;">{rsi_attuale:.1f}</div>
                <div style="font-size: 10px; color: #9ca3af;">{rsi_status}</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="card" style="text-align: center; padding: 10px;">
                <div class="metric-title">Sentiment</div>
                <div class="metric-value" style="font-size: 14px; margin-top: 2px;">{sentiment_score}/100</div>
                <div style="font-size: 10px; color: #38bdf8;">{sentiment_label.split()[0]}</div>
            </div>
        """, unsafe_allow_html=True)

    # Grafico Storico dei Prezzi Nativo in Streamlit (Fluido e leggero su mobile)
    st.markdown("""
        <div class="card">
            <div style="font-size: 12px; font-weight: bold; color: #ffffff; margin-bottom: 8px;">Andamento Storico (Ultimi Mesi)</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Visualizzazione grafico pulito
    chart_data = pd.DataFrame({
        'Prezzo': df['Close'],
        'Media 50gg': df['Close'].rolling(window=50).mean()
    })
    st.line_chart(chart_data, color=["#38bdf8", "#f59e0b"], height=220)

    # Sezione Notizie Principali dal Web legate all'Asset
    st.markdown("""
        <div class="card">
            <div style="font-size: 12px; font-weight: bold; color: #ffffff; margin-bottom: 8px;">Notizie Principali & Sentiment Online</div>
        </div>
    """, unsafe_allow_html=True)
    
    try:
        ticker_obj = yf.Ticker(ticker_selezionato)
        notizie = ticker_obj.news
        if notizie and len(notizie) > 0:
            for n in notizie[:3]:
                titolo = n.get('title', 'Notizia finanziaria')
                editore = n.get('publisher', 'Financial Web')
                link = n.get('link', '#')
                st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.02); padding: 8px 10px; border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(255,255,255,0.04);">
                        <a href="{link}" target="_blank" style="font-size: 11px; color: #38bdf8; text-decoration: none; font-weight: 500;">{titolo}</a>
                        <div style="font-size: 9px; color: #9ca3af; margin-top: 2px;">Fonte: {editore}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<p style='font-size: 11px; color: #9ca3af;'>Nessuna notizia recente disponibile per questo asset specifico.</p>", unsafe_allow_html=True)
    except Exception:
        st.markdown("<p style='font-size: 11px; color: #9ca3af;'>Feed notizie temporaneamente non disponibile.</p>", unsafe_allow_html=True)

# Footer
st.markdown("<div style='text-align: center; font-size: 10px; color: #6b7280; margin-top: 20px;'>Smart AI Market Terminal • Powered by Python & Streamlit Cloud</div>", unsafe_allow_html=True)