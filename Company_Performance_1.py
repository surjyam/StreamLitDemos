import streamlit as st
import pandas as pd
import yfinance as yf
import os
import openai
import requests
import io
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Strategic Intelligence & Stock Tracker", layout="wide")

# --- Header Section ---
st.title("📈 Strategic Intelligence & Stock Price Tracker")

col_header1, col_header2 = st.columns([2, 1])

with col_header1:
    st.markdown("### Report Parameters")
    # Year Range selection for 2022-2025
    year_options = ["2022-2023", "2023-2024", "2024-2025", "2022-2025"]
    selected_range = st.selectbox("Select Fiscal Period:", year_options)
    
    # Parse dates for yfinance
    start_year = selected_range.split("-")[0]
    end_year = selected_range.split("-")[-1]
    # Handle "Full Range" text vs single years
    start_date = f"{start_year if '20' in start_year else '2022'}-01-01"
    end_date = f"{end_year if '20' in end_year else '2025'}-12-31"

with col_header2:
    st.markdown("### API Configuration")
    api_key = st.text_input("Enter OpenAI API Key:", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

st.divider()

# --- Main UI: Inputs ---
st.subheader("Target Companies")
c1, c2, c3 = st.columns(3)
with c1:
    comp_a = st.text_input("Company 1 Ticker (e.g. AAPL):", value="AAPL")
with c2:
    comp_b = st.text_input("Company 2 Ticker (e.g. GOOGL):", value="GOOGL")
with c3:
    comp_c = st.text_input("Company 3 Ticker (e.g. MSFT):", value="MSFT")

# --- Section 1: Stock Price Table ---
st.subheader(f"Daily Stock Prices ({selected_range})")

# Custom headers to mimic a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

@st.cache_data
def get_stock_data(tickers, start, end):
    try:
        # 2026 FIX: Do not pass a session object. 
        # yfinance now uses curl_cffi internally by default.
        data = yf.download(
            tickers=tickers, 
            start=start, 
            end=end, 
            interval="1d",
            group_by='column',
            auto_adjust=True,
            # proxy=None  # Only set this if you are behind a corporate firewall
        )
        
        if data.empty:
            return None
            
        # 2026 FIX: MultiIndex Flattening
        # Recent versions return 'Close' under a MultiIndex if multiple tickers are used.
        if isinstance(data.columns, pd.MultiIndex):
            # We specifically target the 'Close' prices level
            if 'Close' in data.columns.levels[0]:
                data = data['Close']
                
        return data
    except Exception as e:
        st.error(f"Market Fetch Error: {e}")
        return None

if st.button("Load Market Data"):
    tickers = f"{comp_a},{comp_b},{comp_c}"
    stock_list = [t.strip().upper() for t in tickers.split(",")]
    df_prices = get_stock_data(stock_list, start_date, end_date)
    
    if df_prices is not None:
        # --- TAB IMPLEMENTATION ---
        tab_data, tab_chart = st.tabs(["🗃 Raw Data", "📈 Price Trends"])
        
        with tab_data:
            st.markdown("### Daily Adjusted Closing Prices")
            # Fixed height creates the scrollable effect
            st.dataframe(df_prices, height=400, use_container_width=True)
            
        with tab_chart:
            st.markdown(f"### Historical Trends ({selected_range})")
            # st.line_chart automatically uses the Date index for X-axis
            st.line_chart(df_prices, use_container_width=True)
            
        # Download Option
        st.download_button("Download Full CSV", df_prices.to_csv(), "market_data.csv")
    else:
        st.warning("No data found. Please check your Ticker symbols and date range.")

st.divider()

# --- Section 2: Competitive Strategy Generator ---
st.subheader("Generate Strategic Analysis")
if st.button("Run AI Strategy Analysis"):
    if not api_key:
        st.error("Please enter an API Key to generate the strategy report.")
    else:
        with st.spinner("Analyzing market strategies..."):
            try:
                prompt = f"""
                Create a competitive report for {comp_a}, {comp_b}, and {comp_c} for {selected_range}.
                Format as CSV with: "Company Name", "Product Description", "Marketing Strategy", "Financial Summary".
                Return ONLY the raw CSV data.
                """
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}])
                csv_data = response.choices[0].message.content.strip().replace("```csv", "").replace("```", "")
                
                strategy_df = pd.read_csv(io.StringIO(csv_data))
                st.dataframe(strategy_df, use_container_width=True)
                
                st.download_button("📥 Download Strategy CSV", strategy_df.to_csv(index=False), "strategy_report.csv", "text/csv")
            except Exception as e:
                st.error(f"AI Analysis failed: {e}")