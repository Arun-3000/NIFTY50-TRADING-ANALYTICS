import yfinance as yf
import pandas as pd
import os
from datetime import datetime, timedelta

DATA_DIR = "data"

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def get_stock_data(symbol, period="2y"):
    """
    Fetch historical stock data for a given symbol.
    Uses local cache if available and recent, otherwise downloads.
    """
    ensure_data_dir()
    # Format the symbol for filename (replace any problematic characters)
    filename = symbol.replace("^", "").replace(".", "_") + ".csv"
    filepath = os.path.join(DATA_DIR, filename)

    # Check if we have a cached file and if it's from today (or recent)
    if os.path.exists(filepath):
        # Read the cached data
        df = pd.read_csv(filepath, index_col=0, parse_dates=True)
        # Check if the data is up to date (we'll consider up to date if the last date is today or yesterday)
        # Since we are fetching daily data, we can check if the last date is at least yesterday.
        # However, for simplicity, we'll just check if the file exists and is not empty.
        # In a more robust system, we might check the last date and update if needed.
        # For now, we'll always download if the file is older than a day.
        # But let's keep it simple: if the file exists, we use it (assuming we update it weekly or so).
        # To avoid re-downloading every time, we can check the last modified date.
        file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
        if datetime.now() - file_mod_time < timedelta(days=1):
            return df

    # Download data
    print(f"Downloading data for {symbol}...")
    ticker = yf.Ticker(symbol)
    # We download data with auto_adjust=False to get the raw OHLC, but we can adjust later.
    df = ticker.history(period=period, auto_adjust=False)

    if df.empty:
        print(f"No data found for {symbol}")
        return None

    # Save to CSV
    df.to_csv(filepath)
    return df

def get_nifty50_symbols():
    """
    Returns a list of NIFTY 50 stock symbols with .NS suffix.
    This is a static list; in practice, you might fetch from an API or file.
    """
    # List of NIFTY 50 stocks as of a certain date (2024).
    # Note: This list may change over time.
    nifty50 = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "HDFC.NS",
        "ICICIBANK.NS", "KOTAKBANK.NS", "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS",
        "ASIANPAINT.NS", "LT.NS", "AXISBANK.NS", "MARUTI.NS", "SUNPHARMA.NS",
        "TITAN.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "WIPRO.NS", "M&M.NS",
        "NTPC.NS", "POWERGRID.NS", "TECHM.NS", "TATACONSUM.NS", "INDUSINDBK.NS",
        "JSWSTEEL.NS", "HCLTECH.NS", "ADANIENT.NS", "ADANIPORTS.NS", "BRITANNIA.NS",
        "DRREDDY.NS", "CIPLA.NS", "DIVISLAB.NS", "APOLLOHOSP.NS", "EICHERMOT.NS",
        "GRASIM.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "COALINDIA.NS", "ONGC.NS",
        "BAJAJFINSV.NS", "BAJFINANCE.NS", "BPCL.NS", "HDFCLIFE.NS", "SBILIFE.NS",
        "TATAMOTORS.NS", "TATASTEEL.NS", "UPL.NS"
    ]
    return nifty50

if __name__ == "__main__":
    # Test the function
    symbols = get_nifty50_symbols()
    for symbol in symbols[:5]:  # Test first 5
        df = get_stock_data(symbol)
        if df is not None:
            print(f"{symbol}: {df.shape}")