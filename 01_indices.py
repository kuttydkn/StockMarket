import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime
import feedparser
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Indian Stocks: Mojo & MFI Analyzer", layout="wide")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} IST")

# ====================== DATA ======================
global_indices = {
    "S&P 500": "^GSPC", "Dow Jones": "^DJI", "Nasdaq": "^IXIC",
    "FTSE 100": "^FTSE", "DAX": "^GDAXI", "Nikkei 225": "^N225",
    "Hang Seng": "^HSI", "Shanghai": "^SSEC"
}

indian_indices = {
    "Nifty 50": "^NSEI", "Sensex": "^BSESN", "Nifty Bank": "^NSEBANK",
    "Nifty IT": "^CNXIT", "Nifty Auto": "^CNXAUTO", "Nifty FMCG": "^CNXFMCG",
    "Nifty Pharma": "^CNXPHARMA", "Nifty Financial": "^CNXFIN",
    "Nifty Realty": "^CNXREALTY", "Nifty Metal": "^CNXMETAL"
}

commodities = {
    "Gold": "GC=F", "Silver": "SI=F", "Crude Oil": "CL=F",
    "Brent Oil": "BZ=F", "Natural Gas": "NG=F", "Copper": "HG=F"
}

# Major Nifty 50 stocks for gainers/losers
nifty_stocks = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
                "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS", "LT.NS",
                "AXISBANK.NS", "ITC.NS", "ASIANPAINT.NS", "SUNPHARMA.NS", "BAJFINANCE.NS"]

# ====================== SIDEBAR ======================
st.header("Dashboard Settings")
refresh_interval = st.selectbox("Auto Refresh", ["Off", "30 sec", "1 min", "5 min"], index=0)

# ====================== DATA FETCH FUNCTIONS ======================
@st.cache_data(ttl=30)
def fetch_market_data(tickers_dict):
    data = []
    for name, ticker in tickers_dict.items():
        try:
            t = yf.Ticker(ticker)
            info = t.info
            price = info.get('regularMarketPrice') or info.get('currentPrice') or info.get('previousClose')
            prev = info.get('regularMarketPreviousClose') or price
            change = price - prev if price and prev else 0
            change_pct = (change / prev * 100) if prev else 0

            data.append({
                "Name": name,
                "Price": round(price, 2) if price else None,
                "Change": round(change, 2),
                "% Change": round(change_pct, 2),
            })
        except:
            pass
    return pd.DataFrame(data)

@st.cache_data(ttl=60)
def get_top_gainers_losers():
    data = []
    for ticker in nifty_stocks:
        try:
            t = yf.Ticker(ticker)
            info = t.info
            price = info.get('currentPrice') or info.get('regularMarketPrice')
            prev = info.get('previousClose') or info.get('regularMarketPreviousClose')
            if price and prev:
                chg_pct = (price - prev) / prev * 100
                data.append({
                    "Symbol": ticker.replace(".NS", ""),
                    "Price": round(price, 2),
                    "% Change": round(chg_pct, 2),
                    "Volume": info.get('volume', 'N/A')
                })
        except:
            continue
    df = pd.DataFrame(data)
    if not df.empty:
        gainers = df.nlargest(10, '% Change')
        losers = df.nsmallest(10, '% Change')
        return gainers, losers
    return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=300)
def get_market_news():
    try:
        # Get news from Nifty or major stocks
        news = yf.Ticker("^NSEI").news[:15]  # Top 15 news
        return news
    except:
        return []

# ====================== TABS ======================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🌐 Global Indices", "🇮🇳 Indian Indices", "📊 Sectoral + GIFT Nifty",
    "🔥 Top Gainers & Losers", "🛢️ Commodities", "📰 Market News", "Indian ADRs", "Currencies"
])

with tab1:
    st.subheader("Global Market Indices")
    df_global = fetch_market_data({k: global_indices[k] for k in list(global_indices.keys())[:6]})
    st.dataframe(df_global.style.background_gradient(subset=['% Change'], cmap='RdYlGn'), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Indian Market Indices")
    df_ind = fetch_market_data(indian_indices)
    st.dataframe(df_ind.style.background_gradient(subset=['% Change'], cmap='RdYlGn'), use_container_width=True, hide_index=True)

with tab3:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Sectoral Indices")
        df_sec = fetch_market_data(indian_indices)
        st.dataframe(df_sec.style.background_gradient(subset=['% Change'], cmap='RdYlGn'), use_container_width=True, hide_index=True)
    with col2:
        st.subheader("GIFT Nifty")
        try:
            nifty = yf.Ticker("^NSEI").info
            st.metric("GIFT Nifty Indicator", f"{nifty.get('regularMarketPrice', 'N/A')}", 
                     f"{nifty.get('regularMarketChangePercent', 0):.2f}%")
        except:
            st.info("GIFT Nifty data (approximated via Nifty)")

with tab4:  # New Tab - Top Gainers & Losers
    st.subheader("🔥 Nifty 50 Top Gainers & Losers")
    gainers, losers = get_top_gainers_losers()
    
    col_g, col_l = st.columns(2)
    with col_g:
        st.write("**Top Gainers**")
        st.dataframe(gainers.style.background_gradient(subset=['% Change'], cmap='Greens'), use_container_width=True, hide_index=True)
    with col_l:
        st.write("**Top Losers**")
        st.dataframe(losers.style.background_gradient(subset=['% Change'], cmap='Reds'), use_container_width=True, hide_index=True)

with tab5:
    st.subheader("Commodities & Futures")
    df_comm = fetch_market_data(commodities)
    st.dataframe(df_comm.style.background_gradient(subset=['% Change'], cmap='RdYlGn'), use_container_width=True, hide_index=True)

with tab6:  # News Tab - News Feed
    st.subheader("📰 Latest Market News")
    
    feeds = {
        "Economic Times": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "Mint": "https://www.livemint.com/rss/markets",
        "Investing.com India": "https://in.investing.com/rss/news.rss",
        "Moneycontrol": "https://www.moneycontrol.com/rss/MCtopnews.xml",
        "Business Standard - Markets": "https://www.business-standard.com/rss/markets-106.rss"
         }
    
    for name, url in feeds.items():
        st.header(name)
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            st.write(f"**{entry.title}**")
            st.write(entry.link)
            st.write(entry.published)

with tab7:
 # Set page layout
    st.title("🇮🇳 Indian ADRs Real-Time Tracker")
    st.write("Monitor Indian companies listed on US Exchanges (NYSE & NASDAQ).")

    # Dictionary mapping tickers to Company Names
    INDIAN_ADRS = {
        "INFY": "Infosys Ltd.",
        "HDB": "HDFC Bank Ltd.",
        "IBN": "ICICI Bank Ltd.",
        "WIT": "Wipro Ltd.",
        "RDY": "Dr. Reddy's Laboratories",
        "MMYT": "MakeMyTrip Ltd.",
        "SIFY": "Sify Technologies Ltd."
    }

    # Sidebar inputs
    st.header("Settings")
    col1,col2=st.columns(2)
    with col1:
        selected_ticker = st.selectbox("Select ADR", list(INDIAN_ADRS.keys()), format_func=lambda x: f"{x} - {INDIAN_ADRS[x]}")
    with col2:
        time_period = st.selectbox("Select Time Period", ["1d", "5d", "1mo", "6mo", "1y", "5y"], index=2)

    @st.cache_data(ttl=300) # Cache data for 5 minutes to keep it snappy
    def load_adr_data(ticker, period):
        stock = yf.Ticker(ticker)
        
        # Fetch historical data
        df = stock.history(period=period)
        
        # Fetch real-time/current info
        info = stock.info
        return df, info

    try:
        with st.spinner("Fetching market data..."):
            df, info = load_adr_data(selected_ticker, time_period)
            
        # --- Live Metrics Layout ---
        st.header(f"{info.get('longName', INDIAN_ADRS[selected_ticker])} ({selected_ticker})")
        
        current_price = info.get("regularMarketPrice", df['Close'].iloc[-1] if not df.empty else 0)
        previous_close = info.get("regularMarketPreviousClose", df['Close'].iloc[-2] if len(df) > 1 else current_price)
        price_change = current_price - previous_close
        pct_change = (price_change / previous_close) * 100

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Price (USD)", f"${current_price:,.2f}", f"{price_change:+.2f} ({pct_change:+.2f}%)")
        col2.metric("Day High", f"${info.get('dayHigh', df['High'].iloc[-1]):,.2f}")
        col3.metric("Day Low", f"${info.get('dayLow', df['Low'].iloc[-1]):,.2f}")
        col4.metric("Volume", f"{info.get('regularMarketVolume', df['Volume'].iloc[-1]):,}")

        st.markdown("---")

        # --- Interactive Plotly Chart ---
        st.subheader("Price Movement")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], mode='lines', name='Close Price', line=dict(color='#00CC96', width=2)))
        
        fig.update_layout(
            template="plotly_dark",
            xaxis_title="Date/Time",
            yaxis_title="Price (USD)",
            margin=dict(l=20, r=20, t=20, b=20),
            height=450
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Raw Data Expander ---
        with st.expander("View Raw Historical Data"):
            st.dataframe(df.sort_index(ascending=False), use_container_width=True)

    except Exception as e:
        st.error(f"Could not retrieve data for {selected_ticker}. This could be due to a temporary API issue or structural changes with the symbol.")
        st.exception(e)   

with tab8:
    st.title("💱 Live Dollar Index & Major Currencies")
    st.write("Real-time forex tracking powered by Yahoo Finance cross-rates.")

    # 1. Base Tickers to download
    TICKERS = {
        "US Dollar Index": "DX-Y.NYB",
        "EUR/USD (Euro)": "EURUSD=X",
        "USD/JPY (Yen)": "JPY=X",
        "GBP/USD (Pound)": "GBPUSD=X",
        "USD/CAD (Loonie)": "CAD=X",
        "USD/CHF (Swiss Franc)": "CHF=X",
        "AUD/USD (Aussie)": "AUDUSD=X",
        # Underlying legs for synthetic KWD/INR calculation
        "USD/INR": "USDINR=X",
        "KWD/USD": "KWDUSD=X"
    }

    INV_TICKERS = {v: k for k, v in TICKERS.items()}

    try:
        # Fetch 5 days of data for ALL tickers in one shot
        raw_data = yf.download(list(TICKERS.values()), period="5d", group_by="ticker", progress=False)
        
        data_dict = {}
        
        # Extract data series for each pair
        for ticker_symbol in TICKERS.values():
            if ticker_symbol in raw_data.columns.levels[0]:
                data_dict[ticker_symbol] = raw_data[ticker_symbol].dropna()

        # Calculate standard metrics for basic pairs
        live_rows = []
        for display_name, symbol in TICKERS.items():
            if symbol in ["USDINR=X", "KWDUSD=X"]: 
                continue # We skip raw legs here, we show USD/INR as a standard metric if desired
            
            df = data_dict.get(symbol)
            if df is not None and len(df) >= 2:
                latest = df['Close'].iloc[-1]
                prev = df['Close'].iloc[-2]
                change = latest - prev
                pct = (change / prev) * 100
                live_rows.append({"Name": display_name, "Price": round(latest, 4), "Change": round(change, 4), "Pct": f"{pct:+.2f}%"})

        # --- SYNTHETIC KWD/INR CALCULATION ---
        df_usdinr = data_dict.get("USDINR=X")
        df_kwdusd = data_dict.get("KWDUSD=X")
        
        if df_usdinr is not None and df_kwdusd is not None:
            # Align dates to prevent mismatched rows
            combined = pd.DataFrame({
                'USDINR': df_usdinr['Close'],
                'KWDUSD': df_kwdusd['Close']
            }).dropna()
            
            if len(combined) >= 2:
                # Multiplied: (KWD -> USD) * (USD -> INR) = KWD -> INR
                kwd_inr_series = combined['KWDUSD'] * combined['USDINR']
                
                latest_kwd = kwd_inr_series.iloc[-1]
                prev_kwd = kwd_inr_series.iloc[-2]
                change_kwd = latest_kwd - prev_kwd
                pct_kwd = (change_kwd / prev_kwd) * 100
                
                # Insert Kuwaiti Dinar right into our metrics list
                live_rows.insert(4, {
                    "Name": "KWD/INR (Kuwaiti Dinar)",
                    "Price": round(latest_kwd, 2), # 2 decimal places standard for INR
                    "Change": round(change_kwd, 2),
                    "Pct": f"{pct_kwd:+.2f}%"
                })
                
        # Also add USD/INR natively as a metric card
        if df_usdinr is not None and len(df_usdinr) >= 2:
            latest = df_usdinr['Close'].iloc[-1]
            prev = df_usdinr['Close'].iloc[-2]
            change = latest - prev
            pct = (change / prev) * 100
            live_rows.append({"Name": "USD/INR (Rupee)", "Price": round(latest, 4), "Change": round(change, 4), "Pct": f"{pct:+.2f}%"})

        # Render Metric Cards Grid
        df_live = pd.DataFrame(live_rows)
        if not df_live.empty:
            row_size = 4
            for i in range(0, len(df_live), row_size):
                chunk = df_live.iloc[i:i+row_size].reset_index()
                cols = st.columns(len(chunk))
                for index, row in chunk.iterrows():
                    with cols[index]:
                        st.metric(label=row["Name"], value=f"{row['Price']}", delta=f"{row['Change']} ({row['Pct']})")

    except Exception as e:
        st.error(f"Failed to extract market rates: {e}")

    st.markdown("---")

    # 4. Interactive Historical Charts Section
    st.subheader("📈 Historical Trends")

    col_select, col_chart = st.columns([1, 3])

    # Create user select choices list
    chart_options = list(TICKERS.keys())
    chart_options.remove("USD/INR")
    chart_options.remove("KWD/USD")
    chart_options.insert(4, "KWD/INR (Kuwaiti Dinar)")

    with col_select:
        selected_name = st.selectbox("Select Currency / Index to view:", chart_options)
        time_frame = st.selectbox("Select Timeframe:", ["1mo", "3mo", "6mo", "1y", "5y"], index=2)

    with col_chart:
        try:
            if selected_name == "KWD/INR (Kuwaiti Dinar)":
                # 1. Fetch historical windows explicitly flattening the multi-index format
                raw_usdinr = yf.download("USDINR=X", period=time_frame, progress=False)["Close"]
                raw_kwdusd = yf.download("KWDUSD=X", period=time_frame, progress=False)["Close"]
                
                # 2. Convert multi-index columns into a flat Series if needed
                s_usdinr = raw_usdinr.squeeze()
                s_kwdusd = raw_kwdusd.squeeze()
                
                # 3. Combine timelines cleanly over matching calendar dates
                chart_df = pd.DataFrame({
                    'USDINR': s_usdinr,
                    'KWDUSD': s_kwdusd
                }).dropna()
                
                # 4. Multiply cross-rates
                chart_series = chart_df['KWDUSD'] * chart_df['USDINR']
                st.line_chart(chart_series, y_label="INR per 1 KWD", use_container_width=True)
                
            else:
                selected_ticker = TICKERS[selected_name]
                # Flatten regular tickers too to keep Streamlit charting seamless
                hist_df = yf.download(selected_ticker, period=time_frame, progress=False)["Close"].squeeze()
                st.line_chart(hist_df, y_label="Price / Value", use_container_width=True)
                
        except Exception as chart_error:
            st.error(f"Could not construct chart: {chart_error}")
    # ====================== CHARTS ======================
    st.subheader("📈 Recent Price Trends (5 Days)")
    symbols = list(global_indices.values())[:3] + list(indian_indices.values())[:3] + list(commodities.values())[:2]
    data = yf.download(symbols, period="5d")['Close']
    fig = px.line(data, x=data.index, y=data.columns, title="Multi-Asset Price Movement")
    st.plotly_chart(fig, use_container_width=True)

# ====================== CONTROLS ======================
col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    if st.button("🔄 Refresh All Data"):
        st.rerun()

if refresh_interval != "Off":
    secs = {"30 sec": 30, "1 min": 60, "5 min": 300}[refresh_interval]
    time.sleep(secs)
    st.rerun()

st.caption("Data Source: Yahoo Finance • yfinance | Note: For more accurate NSE gainers, consider nsepython or official API in production.")