#stock_news_app.py
#
# This is a Python script that provides the foundation for your stock news app.
#
# --- PREREQUISITES ---
# You MUST install the required libraries first by running:
# pip install pandas newsapi-python nsetools
## 
# --- IMPORTANT SETUP ---
# 1. You MUST get a free API key from https://newsapi.org/
# 2. Paste your API key in the `CONFIG` section below.

import pandas as pd
from newsapi import NewsApiClient
from nsetools import Nse
from datetime import datetime, timedelta
import json

# --- 1. CONFIGURATION ---
# !IMPORTANT!: Paste your NewsAPI key here
NEWS_API_KEY = "YOUR_API_KEY_HERE"  # Replace with your actual key

# --- 2. STOCK LIST FUNCTIONS ---
# These functions get the lists of stocks you requested.

def get_fno_stocks():
    """
    Fetches the current list of F&O (Futures & Options) stocks
    from the NSE website.
    """
    print("Fetching F&O stock list...")
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
        
        print(f"Found {len(stock_list)} F&O stocks.")
        return stock_list
    except Exception as e:
        print(f"Error fetching F&O stocks: {e}")
        print("Please check your internet connection or the NSE URL.")
        return []

def get_index_stocks(index_name):
    """
    A helper function to get all stock symbols for a given Nifty index
    using the 'nsetools' library.
    
    Valid index_name examples: 'NIFTY 50', 'NIFTY MIDCAP 150', 'NIFTY SMALLCAP 250'
    """
    print(f"Fetching stock list for {index_name}...")
    try:
        nse = Nse()
        # get_stock_codes() on its own is unreliable, get_index_quote is better
        # A more robust way is to get the list for an index
        if not nse.is_valid_index(index_name):
            print(f"Error: Invalid index name '{index_name}'.")
            print(f"Valid indices include: {', '.join(nse.get_index_list())}")
            return []
            
        stock_list = nse.get_stocks_in_index(index_name)
        
        if not stock_list:
            print(f"No stocks returned for {index_name}. The library may need an update or the index name is wrong.")
            return []
            
        print(f"Found {len(stock_list)} stocks in {index_name}.")
        return [stock.upper() for stock in stock_list]
    except Exception as e:
        print(f"Error fetching index stocks: {e}")
        return []

def get_largecap_stocks():
    """Fetches Large Cap stocks (e.g., Nifty 100)"""
    # You can change this to 'NIFTY 50' or other large-cap index
    return get_index_stocks("NIFTY 100")

def get_midcap_stocks():
    """Fetches Mid Cap stocks (e.g., Nifty Midcap 150)"""
    return get_index_stocks("NIFTY MIDCAP 150")

def get_smallcap_stocks():
    """Fetches Small Cap stocks (e.g., Nifty Smallcap 250)"""
    return get_index_stocks("NIFTY SMALLCAP 250")

# --- 3. DATE HELPER FUNCTIONS ---
# These functions calculate the 'from' and 'to' dates for the API.

def get_date_range(period_name):
    """
    Returns a (from_date, to_date) tuple in ISO format (YYYY-MM-DD)
    based on the period name.
    """
    today = datetime.now()
    
    if period_name == "last_week":
        from_date = today - timedelta(days=7)
    elif period_name == "last_4_weeks":
        from_date = today - timedelta(weeks=4)
    elif period_name == "last_3_months":
        # Using 90 days as an approximation for 3 months
        from_date = today - timedelta(days=90)
    elif period_name == "last_6_months":
        # Using 180 days as an approximation for 6 months
        from_date = today - timedelta(days=180)
    else:
        # Default to last 7 days
        from_date = today - timedelta(days=7)

    # Format dates as 'YYYY-MM-DD' strings
    return from_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")

# --- 4. NEWS API FUNCTION ---

def fetch_news_for_stocks(stock_list, from_date, to_date):
    """
    Fetches news articles for a given list of stocks within a date range.
    """
    if NEWS_API_KEY == "YOUR_API_KEY_HERE":
        print("="*50)
        print("ERROR: Please update the 'NEWS_API_KEY' variable")
        print("in the CONFIG section (line 21) with your key from newsapi.org.")
        print("="*50)
        return

    if not stock_list:
        print("No stock list provided. Skipping news fetch.")
        return

    # --- NewsAPI Query Limitation ---
    # NewsAPI has a limit on query length (1024 chars on free plan).
    # We cannot OR all 500+ stocks.
    # Strategy: We take the first 10-15 stocks and create a query.
    # A better app would fetch news for each stock individually or in small batches.
    
    stocks_for_query = stock_list[:15] # Take the first 15 stocks
    
    # Create a query like: "(RELIANCE OR TCS OR INFY) AND (stock OR NSE OR BSE)"
    # We add terms like "stock" or "NSE" to focus the search.
    query = f"({' OR '.join(stocks_for_query)}) AND (stock OR market OR NSE OR BSE)"

    print(f"\n--- Fetching News ---")
    print(f"Query: {query}")
    print(f"From: {from_date} To: {to_date}")
    
    try:
        newsapi = NewsApiClient(api_key=NEWS_API_KEY)
        
        all_articles = newsapi.get_everything(
            q=query,
            from_param=from_date,
            to=to_date,
            language='en',
            sort_by='publishedAt', # You can also use 'relevancy' or 'popularity'
            page_size=20 # Get top 20 articles
        )
        
        print(f"\nFound {all_articles['totalResults']} total articles.")
        
        if all_articles['totalResults'] == 0:
            print("No news found for this query and date range.")
            return

        # Print the top 5 articles
        print("\n--- Top 5 Articles ---")
        for i, article in enumerate(all_articles['articles'][:5]):
            print(f"\n{i+1}. {article['title']}")
            print(f"   Source: {article['source']['name']}")
            print(f"   Date: {article['publishedAt']}")
            print(f"   URL: {article['url']}")

    except Exception as e:
        print(f"Error fetching news from NewsAPI: {e}")
        if "apiKeyInvalid" in str(e):
            print(">>> Your API key is invalid. Please check it.")
        elif "rateLimited" in str(e):
            print(">>> You are being rate-limited. Try again later.")


# --- 5. MAIN APPLICATION MENU ---

def main():
    """
    Runs the main application loop.
    """
    print("="*30)
    print("  Stock News Fetcher")
    print("="*30)
    
    while True:
        print("\n--- Main Menu ---")
        print("Stock Lists:")
        print("  1. F&O Stocks")
        print("  2. Large-Cap Stocks (NIFTY 100)")
        print("  3. Mid-Cap Stocks (NIFTY MIDCAP 150)")
        print("  4. Small-Cap Stocks (NIFTY SMALLCAP 250)")
        print("\n  0. Exit")
        
        choice = input("Select a stock list to get news for: ")
        
        stock_list = []
        if choice == '1':
            stock_list = get_fno_stocks()
        elif choice == '2':
            stock_list = get_largecap_stocks()
        elif choice == '3':
            stock_list = get_midcap_stocks()
        elif choice == '4':
            stock_list = get_smallcap_stocks()
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
            continue
            
        if not stock_list:
            print("Could not retrieve stock list. Please try again.")
            continue
            
        # --- Date Period Menu ---
        print("\nSelect a time period for news:")
        print("  a. Last Week (7 days)")
        print("  b. Last 4 Weeks")
        print("  c. Last 3 Months")
        print("  d. Last 6 Months")
        
        period_choice = input("Select a time period: ").lower()
        
        if period_choice == 'a':
            period = "last_week"
        elif period_choice == 'b':
            period = "last_4_weeks"
        elif period_choice == 'c':
            period = "last_3_months"
        elif period_choice == 'd':
            period = "last_6_months"
        else:
            print("Invalid period. Defaulting to 'Last Week'.")
            period = "last_week"
            
        # Get the date range
        from_date, to_date = get_date_range(period)
        
        # Fetch and display the news
        fetch_news_for_stocks(stock_list, from_date, to_date)
        
        input("\nPress Enter to return to the main menu...")

# Run the main function when the script is executed
if __name__ == "__main__":
    main()
