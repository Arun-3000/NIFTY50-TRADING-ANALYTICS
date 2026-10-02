import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_fetcher import get_stock_data, get_nifty50_symbols
from indicators import add_all_indicators, flag_breakout

# Set page config
st.set_page_config(layout="wide", page_title="SEBI Trading Analytics Dashboard")

# Title
st.title("NIFTY 50 Trading Analytics Dashboard")

# Sidebar
st.sidebar.header("Controls")
refresh_button = st.sidebar.button("Refresh Data")
show_details = st.sidebar.checkbox("Show Stock Details", value=True)

# Cache the data fetching and indicator calculation
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_and_process_data(symbol):
    df = get_stock_data(symbol)
    if df is None or df.empty:
        return None
    df = add_all_indicators(df)
    return df

# Get NIFTY 50 symbols
symbols = get_nifty50_symbols()

# Fetch and process data for all symbols
breakout_stocks = []
stock_data = {}  # To store dataframes for details

progress_bar = st.progress(0)
status_text = st.empty()

for i, symbol in enumerate(symbols):
    status_text.text(f"Processing {symbol} ({i+1}/{len(symbols)})")
    df = load_and_process_data(symbol)
    if df is not None:
        stock_data[symbol] = df
        if flag_breakout(df):
            breakout_stocks.append(symbol)
    progress_bar.progress((i + 1) / len(symbols))

status_text.text("Done!")

# Display breakout stocks
st.header("Breakout Stocks (Close > SMA50 & Volume > Volume MA20)")
if breakout_stocks:
    breakout_df = pd.DataFrame({
        "Symbol": breakout_stocks,
        "Latest Close": [stock_data[sym]['Close'].iloc[-1] for sym in breakout_stocks],
        "SMA50": [stock_data[sym]['SMA_50'].iloc[-1] for sym in breakout_stocks],
        "Volume Ratio": [stock_data[sym]['Volume_Ratio'].iloc[-1] for sym in breakout_stocks],
        "RSI (14)": [stock_data[sym]['RSI'].iloc[-1] for sym in breakout_stocks]
    })
    st.dataframe(breakout_df.style.format({
        "Latest Close": "{:.2f}",
        "SMA50": "{:.2f}",
        "Volume Ratio": "{:.2f}",
        "RSI (14)": "{:.2f}"
    }), height=min(400, len(breakout_stocks)*35+38))
else:
    st.write("No breakout stocks found.")

# Show details for selected stock
if show_details and breakout_stocks:
    st.header("Stock Details")
    selected_symbol = st.selectbox("Select a stock to view details", breakout_stocks)

    if selected_symbol in stock_data:
        df = stock_data[selected_symbol]

        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=('Price & Moving Averages', 'RSI (14)', 'Volume'),
            row_heights=[0.5, 0.2, 0.3]
        )

        # Price and moving averages
        fig.add_trace(go.Candlestick(x=df.index,
                                     open=df['Open'],
                                     high=df['High'],
                                     low=df['Low'],
                                     close=df['Close'],
                                     name="Price"), row=1, col=1)

        # Add moving averages
        for ma in ['SMA_20', 'SMA_50', 'SMA_200']:
            if ma in df.columns:
                fig.add_trace(go.Line(x=df.index, y=df[ma], name=ma), row=1, col=1)

        # RSI
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], name="RSI", line=dict(color='purple')), row=2, col=1)
        # Add RSI overbought/oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        # Volume
        fig.add_trace(go.Bar(x=df.index, y=df['Volume'], name="Volume", marker_color='blue'), row=3, col=1)
        # Volume MA
        if 'Volume_MA' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['Volume_MA'], name="Volume MA", line=dict(color='orange')), row=3, col=1)

        # Update layout
        fig.update_layout(height=800, showlegend=True, xaxis_rangeslider_visible=False)
        fig.update_yaxes(title_text="Price (INR)", row=1, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1, range=[0, 100])
        fig.update_yaxes(title_text="Volume", row=3, col=1)

        st.plotly_chart(fig, use_container_width=True)

        # Show latest indicators
        st.subheader("Latest Indicators")
        latest = df.iloc[-1]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Close", f"{latest['Close']:.2f}")
        col2.metric("SMA50", f"{latest['SMA_50']:.2f}")
        col3.metric("RSI (14)", f"{latest['RSI']:.2f}")
        col4.metric("Volume Ratio", f"{latest['Volume_Ratio']:.2f}")

# Footer
st.sidebar.markdown("---")
st.sidebar.info(
    "Data sourced from Yahoo Finance via yfinance. "
    "Historical data is cached locally to avoid repeated downloads."
)