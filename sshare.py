# stock_news_app.py
#
# This is a Streamlit web application for your stock news app.
#
# --- PREREQUISITES ---
# You MUST install the required libraries first by running in your terminal:
# pip install streamlit pandas newsapi-python nsetools
#
# --- HOW TO RUN ---
# 1. Save this file as stock_news_app.py
# 2. Open your terminal
# 3. Run: streamlit run stock_news_app.py
# 4. Your browser will automatically open with the app.
#
# --- IMPORTANT SETUP ---
# 1. You MUST get a free API key from https://newsapi.org/
# 2. Paste your API key into the text box in the app's sidebar.

import pandas as pd
from newsapi import NewsApiClient
from nsetools import Nse
from datetime import datetime, timedelta
import streamlit as st

# --- 1. STOCK LIST FUNCTIONS (with Caching) ---
# @st.cache_data tells Streamlit to store the result of these functions
# so we don't re-download the list every time the app refreshes.

@st.cache_data
def get_fno_stocks():
    """
    Fetches the current list of F&O (Futures & Options) stocks
    from the NSE website.
    """
    st.write("Cache miss: Fetching F&O stock list...")
    try:
        # This URL points to the official NSE CSV file for F&O market lots
        fno_csv_url = "https://archives.nseindia.com/content/fo/fo_mktlots.csv"
        
        # Read the CSV file directly using pandas
        # We skip the first row (index 0) which is a header
        df = pd.read_csv(fno_csv_url, skiprows=1)
        
        # The stock symbols are in the second column (index 1)
        # We'll get the column name from the data itself
        symbol_column = df.columns[1]
        
        # Get the list of symbols, convert to uppercase, and remove any whitespace
        stock_list = df[symbol_column].str.strip().str.upper().tolist()
        
        st.write(f"Found {len(stock_list)} F&O stocks.")
        return stock_list
    except Exception as e:
        st.error(f"Error fetching F&O stocks: {e}")
        st.warning("Could not fetch F&O list. Using a small backup list.")
        return ["RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK"] # Fallback

@st.cache_data
def get_index_stocks(index_name):
    """
    A helper function to get all stock symbols for a given Nifty index
    using the 'nsetools' library.
    
    Valid index_name examples: 'NIFTY 50', 'NIFTY MIDCAP 150', 'NIFTY SMALLCAP 250'
    """
    st.write(f"Cache miss: Fetching stock list for {index_name}...")
    try:
        nse = Nse()
        if not nse.is_valid_index(index_name):
            st.error(f"Error: Invalid index name '{index_name}'.")
            valid_indices = nse.get_index_list()
            st.info(f"Valid indices include: {', '.join(valid_indices)}")
            return []
            
        stock_list = nse.get_stocks_in_index(index_name)
        
        if not stock_list:
            st.warning(f"No stocks returned for {index_name}. Library may be out of date.")
            return []
            
        st.write(f"Found {len(stock_list)} stocks in {index_name}.")
        return [stock.upper() for stock in stock_list]
    except Exception as e:
        st.error(f"Error fetching index stocks: {e}")
        return []

def get_midcap_stocks():
    """Fetches Mid Cap stocks (e.g., Nifty Midcap 150)"""
    # You can change this to "NIFTY MIDCAP 50" or "NIFTY MIDCAP 100" if you prefer
    return get_index_stocks("NIFTY MIDCAP 150")

# --- 2. DATE HELPER FUNCTIONS ---

def get_date_range(period_name):
    """
    Returns a (from_date, to_date) tuple in ISO format (YYYY-MM-DD)
    based on the period name.
    """
    today = datetime.now()
    
    if period_name == "last_week":
        from_date = today - timedelta(days=7)
    elif period_name == "one_month":
        from_date = today - timedelta(days=30) # Approx 1 month
    elif period_name == "three_months":
        from_date = today - timedelta(days=90) # Approx 3 months
    else:
        from_date = today - timedelta(days=7) # Default

    return from_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

# --- 3. NEWS API FUNCTION ---

def fetch_news_for_stocks(api_key, stock_list, from_date, to_date):
    """
    Fetches news articles for a given list of stocks within a date range.
    Returns a list of articles.
    """
    if not api_key:
        st.sidebar.error("API key is missing. Please enter it above.")
        return []

    if not stock_list:
        st.warning("No stock list provided. Skipping news fetch.")
        return []

    # --- NewsAPI Query Limitation ---
    # We take the first 10-15 stocks to build a query.
    # NewsAPI queries get too long otherwise.
    stocks_for_query = stock_list[:15]
    # We add (stock OR market) to find more relevant articles
    query = f"({' OR '.join(stocks_for_query)}) AND (stock OR market OR NSE OR BSE)"

    st.write(f"Fetching news with query: {query[:100]}...")
    st.write(f"Date Range: {from_date} to {to_date}")
    
    try:
        newsapi = NewsApiClient(api_key=api_key)
        
        with st.spinner(f"Searching for news..."):
            all_articles = newsapi.get_everything(
                q=query,
                from_param=from_date,
                to=to_date,
                language='en',
                sort_by='publishedAt',
                page_size=50 # Get up to 50 articles
            )
        
        st.success(f"Found {all_articles['totalResults']} total articles.")
        
        if all_articles['totalResults'] == 0:
            st.info("No news found for this query and date range.")
            return []

        return all_articles['articles']

    except Exception as e:
        st.error(f"Error fetching news from NewsAPI: {e}")
        if "apiKeyInvalid" in str(e):
            st.error("Your API key is invalid. Please check it.")
        elif "rateLimited" in str(e):
            st.error("You are being rate-limited. Try again later.")
        return []


# --- 4. STREAMLIT APP UI ---

# Set wide layout
st.set_page_config(layout="wide")

# Title
st.title("Stock News Dashboard")
st.write("Fetches stock lists and searches for relevant news.")

# --- Sidebar Controls ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your NewsAPI Key", type="password")

st.sidebar.header("Filters")

# Stock list selection
stock_list_options = {
    "F&O Stocks": get_fno_stocks,
    "Mid-Cap (NIFTY MIDCAP 150)": get_midcap_stocks,
    # You can add more lists here
}
stock_list_label = st.sidebar.selectbox(
    "1. Select Stock List",
    options=list(stock_list_options.keys())
)

# Date period selection
period_options = {
    "Last Week": "last_week",
    "One Month": "one_month",
    "Three Months": "three_months",
}
period_label = st.sidebar.selectbox(
    "2. Select Time Period",
    options=list(period_options.keys())
)

# Fetch button
if st.sidebar.button("Get News", type="primary"):
    
    if not api_key:
        st.sidebar.error("Please enter your NewsAPI key above.")
        st.stop() # Stop execution if no API key

    # 1. Get stock list
    with st.spinner(f"Fetching {stock_list_label} list..."):
        stock_list_func = stock_list_options[stock_list_label]
        stock_list = stock_list_func()
    
    if not stock_list:
        st.error("Could not retrieve stock list. Halting.")
        st.stop()
    
    st.success(f"Successfully fetched {len(stock_list)} stocks.")

    # 2. Get date range
    period_key = period_options[period_label]
    from_date, to_date = get_date_range(period_key)

    # 3. Fetch news
    articles = fetch_news_for_stocks(api_key, stock_list, from_date, to_date)

    # 4. Display articles
    if articles:
        st.subheader(f"Showing Top {len(articles)} Articles")
        
        for article in articles:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{article['title']}**")
                    st.write(f"Source: {article['source']['name']} | Published: {pd.to_datetime(article['publishedAt']).strftime('%d-%b-%Y %H:%M')}")
                    
                    if article['description']:
                        st.write(article['description'])
                        
                    st.markdown(f"[Read Full Article]({article['url']})", unsafe_allow_html=True)
                with col2:
                    if article['urlToImage']:
                        st.image(article['urlToImage'], use_column_width=True)
    else:
        st.info("No articles found to display.")

else:
    st.info("Configure your settings in the sidebar and press 'Get News'.")

