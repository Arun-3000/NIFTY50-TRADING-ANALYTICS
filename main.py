import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from plotly.subplots import make_subplots
from datetime import date

from data_fetcher import get_stock_data, get_nifty50_symbols
from indicators import add_all_indicators, flag_breakout


# =====================================================
# PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="NIFTY 50 Complete Trading Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📈 NIFTY 50 Complete Trading Analytics")
st.caption(
    "Historical Stock Data | Technical Analysis | "
    "Market Scanner | Data Export"
)


# =====================================================
# CUSTOM STYLE
# =====================================================

st.markdown("""
<style>
[data-testid="stMetric"] {
    background-color: rgba(128,128,128,0.08);
    padding: 15px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("⚙️ Dashboard Controls")

if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

show_all_history = st.sidebar.checkbox(
    "Show complete available history",
    value=True
)

show_raw_data = st.sidebar.checkbox(
    "Show raw OHLCV data",
    value=True
)

show_indicators = st.sidebar.checkbox(
    "Show technical indicators",
    value=True
)


# =====================================================
# LOAD STOCK DATA
# =====================================================

@st.cache_data(ttl=3600, show_spinner=False)
def load_stock_data(symbol):

    try:
        df = get_stock_data(symbol, period="max")

        if df is None or df.empty:
            return None

        df = df.copy()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df.columns = [
            str(col).strip().replace(" ", "_")
            for col in df.columns
        ]

        if "Close" not in df.columns:
            return None

        df = df.loc[
            ~df.index.duplicated(keep="last")
        ].sort_index()

        df = add_all_indicators(df)

        return df

    except Exception as e:
        return None


# =====================================================
# GET STOCK SYMBOLS
# =====================================================

symbols = get_nifty50_symbols()

if not symbols:
    st.error("No stock symbols were found.")
    st.stop()

st.sidebar.metric("Stocks in configured list", len(symbols))


# =====================================================
# FETCH ALL STOCKS
# =====================================================

stock_data = {}
failed_stocks = []

progress = st.progress(0)
status = st.empty()

for i, symbol in enumerate(symbols):

    status.text(
        f"Loading {symbol} ({i + 1}/{len(symbols)})"
    )

    df = load_stock_data(symbol)

    if df is not None and not df.empty:
        stock_data[symbol] = df
    else:
        failed_stocks.append(symbol)

    progress.progress((i + 1) / len(symbols))

progress.empty()
status.empty()

if not stock_data:
    st.error(
        "No stock data could be loaded. "
        "Check data_fetcher.py and your internet connection."
    )
    st.stop()


# =====================================================
# CREATE LATEST STOCK SUMMARY
# =====================================================

summary = []

for symbol, df in stock_data.items():

    latest = df.iloc[-1]

    previous_close = (
        df["Close"].iloc[-2]
        if len(df) > 1 else latest["Close"]
    )

    change = latest["Close"] - previous_close

    change_percent = (
        (change / previous_close) * 100
        if previous_close else 0
    )

    summary.append({
        "Symbol": symbol,
        "Date": str(df.index[-1].date()),
        "Close": latest.get("Close", np.nan),
        "Change": change,
        "Change %": change_percent,
        "Open": latest.get("Open", np.nan),
        "High": latest.get("High", np.nan),
        "Low": latest.get("Low", np.nan),
        "Volume": latest.get("Volume", np.nan),
        "SMA 20": latest.get("SMA_20", np.nan),
        "SMA 50": latest.get("SMA_50", np.nan),
        "SMA 200": latest.get("SMA_200", np.nan),
        "RSI": latest.get("RSI", np.nan),
        "Volume Ratio": latest.get("Volume_Ratio", np.nan)
    })

summary_df = pd.DataFrame(summary)


# =====================================================
# TOP LEVEL METRICS
# =====================================================

total_stocks = len(stock_data)

advancing = int((summary_df["Change"] > 0).sum())
declining = int((summary_df["Change"] < 0).sum())

col1, col2, col3, col4 = st.columns(4)

col1.metric("Stocks Loaded", total_stocks)
col2.metric("Advancing", advancing)
col3.metric("Declining", declining)
col4.metric(
    "Average Change",
    f"{summary_df['Change %'].mean():.2f}%"
)


# =====================================================
# DASHBOARD TABS
# =====================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Market Overview",
    "🔍 Individual Stock",
    "🚀 Breakout Scanner",
    "📚 Historical Data",
    "⬇️ Download Data"
])


# =====================================================
# TAB 1: MARKET OVERVIEW
# =====================================================

with tab1:

    st.header("All Available NIFTY 50 Stock Data")

    search = st.text_input(
        "Search stock symbol",
        placeholder="Example: RELIANCE"
    )

    filtered_summary = summary_df.copy()

    if search:
        filtered_summary = filtered_summary[
            filtered_summary["Symbol"].str.contains(
                search, case=False, na=False
            )
        ]

    sort_column = st.selectbox(
        "Sort stocks by",
        ["Change %", "Close", "Volume", "RSI", "Symbol"]
    )

    ascending = st.checkbox(
        "Ascending order",
        value=False
    )

    filtered_summary = filtered_summary.sort_values(
        sort_column,
        ascending=ascending
    )

    st.dataframe(
        filtered_summary,
        use_container_width=True,
        hide_index=True,
        height=550
    )

    st.download_button(
        "Download All Stock Summary CSV",
        data=filtered_summary.to_csv(index=False),
        file_name="nifty50_stock_summary.csv",
        mime="text/csv"
    )

    st.subheader("Stock Price Change")

    chart_df = summary_df.sort_values("Change %")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=chart_df["Symbol"],
            y=chart_df["Change %"],
            name="Daily Change %"
        )
    )

    fig.update_layout(
        title="Latest Available Price Change",
        xaxis_title="Stock",
        yaxis_title="Change (%)",
        height=500,
        xaxis_tickangle=-60
    )

    st.plotly_chart(fig, use_container_width=True)


# =====================================================
# TAB 2: INDIVIDUAL STOCK ANALYSIS
# =====================================================

with tab2:

    st.header("Complete Individual Stock Analysis")

    selected_symbol = st.selectbox(
        "Select a stock",
        list(stock_data.keys())
    )

    df = stock_data[selected_symbol].copy()

    st.subheader(selected_symbol)

    # Date filter

    min_date = df.index.min().date()
    max_date = df.index.max().date()

    date_range = st.date_input(
        "Select historical date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:

        start_date, end_date = date_range

        filtered_df = df.loc[
            (df.index.date >= start_date) &
            (df.index.date <= end_date)
        ].copy()

    else:
        filtered_df = df.copy()

    if filtered_df.empty:
        st.warning("No records available for this date range.")
    else:

        latest = filtered_df.iloc[-1]

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Latest Close",
            f"₹{latest['Close']:,.2f}"
        )

        c2.metric(
            "SMA 50",
            f"₹{latest['SMA_50']:,.2f}"
            if pd.notna(latest.get("SMA_50"))
            else "N/A"
        )

        c3.metric(
            "RSI",
            f"{latest['RSI']:.2f}"
            if pd.notna(latest.get("RSI"))
            else "N/A"
        )

        c4.metric(
            "Volume",
            f"{latest['Volume']:,.0f}"
        )

        # Candlestick and indicator charts

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            row_heights=[0.60, 0.20, 0.20],
            subplot_titles=(
                "Price and Moving Averages",
                "RSI",
                "Volume"
            )
        )

        fig.add_trace(
            go.Candlestick(
                x=filtered_df.index,
                open=filtered_df["Open"],
                high=filtered_df["High"],
                low=filtered_df["Low"],
                close=filtered_df["Close"],
                name="Price"
            ),
            row=1,
            col=1
        )

        if show_indicators:

            for column, label in [
                ("SMA_20", "SMA 20"),
                ("SMA_50", "SMA 50"),
                ("SMA_200", "SMA 200")
            ]:

                if column in filtered_df.columns:

                    fig.add_trace(
                        go.Scatter(
                            x=filtered_df.index,
                            y=filtered_df[column],
                            name=label,
                            mode="lines"
                        ),
                        row=1,
                        col=1
                    )

        if "RSI" in filtered_df.columns:

            fig.add_trace(
                go.Scatter(
                    x=filtered_df.index,
                    y=filtered_df["RSI"],
                    name="RSI",
                    mode="lines"
                ),
                row=2,
                col=1
            )

            fig.add_hline(
                y=70,
                line_dash="dash",
                row=2,
                col=1
            )

            fig.add_hline(
                y=30,
                line_dash="dash",
                row=2,
                col=1
            )

        fig.add_trace(
            go.Bar(
                x=filtered_df.index,
                y=filtered_df["Volume"],
                name="Volume"
            ),
            row=3,
            col=1
        )

        fig.update_layout(
            height=850,
            xaxis_rangeslider_visible=False,
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.subheader("Latest Technical Indicators")

        indicator_columns = [
            c for c in [
                "Open", "High", "Low", "Close",
                "Volume", "SMA_20", "SMA_50",
                "SMA_200", "RSI", "Volume_Ratio",
                "MACD", "MACD_Signal"
            ]
            if c in filtered_df.columns
        ]

        st.dataframe(
            filtered_df[indicator_columns].tail(20),
            use_container_width=True
        )


# =====================================================
# TAB 3: BREAKOUT SCANNER
# =====================================================

with tab3:

    st.header("Technical Breakout Scanner")

    breakout_results = []

    for symbol, df in stock_data.items():

        try:

            result = flag_breakout(df)

            if result:

                latest = df.iloc[-1]

                breakout_results.append({
                    "Symbol": symbol,
                    "Close": latest["Close"],
                    "SMA 50": latest.get("SMA_50", np.nan),
                    "RSI": latest.get("RSI", np.nan),
                    "Volume Ratio": latest.get(
                        "Volume_Ratio", np.nan
                    )
                })

        except Exception:
            continue

    if breakout_results:

        breakout_df = pd.DataFrame(breakout_results)

        st.dataframe(
            breakout_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download Breakout Stocks",
            data=breakout_df.to_csv(index=False),
            file_name="breakout_stocks.csv",
            mime="text/csv"
        )

    else:

        st.info(
            "No stocks currently satisfy the configured "
            "breakout conditions, or the scanner returned no results."
        )


# =====================================================
# TAB 4: COMPLETE HISTORICAL DATA
# =====================================================

with tab4:

    st.header("Historical Market Database")

    historical_symbol = st.selectbox(
        "Choose stock for historical records",
        list(stock_data.keys()),
        key="historical_symbol"
    )

    history_df = stock_data[historical_symbol].copy()

    st.write(
        f"Available records: {len(history_df):,}"
    )

    st.write(
        f"First available date: {history_df.index.min().date()}"
    )

    st.write(
        f"Last available date: {history_df.index.max().date()}"
    )

    if show_all_history:

        display_history = history_df
    else:

        display_history = history_df.tail(100)

    st.dataframe(
        display_history,
        use_container_width=True,
        height=600
    )

    st.download_button(
        "Download Complete Historical Data",
        data=history_df.to_csv(index=True),
        file_name=f"{historical_symbol}_historical_data.csv",
        mime="text/csv"
    )


# =====================================================
# TAB 5: DOWNLOAD ALL DATA
# =====================================================

with tab5:

    st.header("Export Complete Available Stock Database")

    st.write(
        "Combine the historical records loaded for all available "
        "stocks into one downloadable dataset."
    )

    all_records = []

    for symbol, df in stock_data.items():

        export_df = df.copy()

        export_df["Symbol"] = symbol

        export_df.index.name = "Date"

        export_df = export_df.reset_index()

        all_records.append(export_df)

    if all_records:

        master_df = pd.concat(
            all_records,
            ignore_index=True
        )

        st.metric(
            "Total Historical Records",
            f"{len(master_df):,}"
        )

        st.metric(
            "Stocks Included",
            master_df["Symbol"].nunique()
        )

        st.subheader("Master Dataset Preview")

        st.dataframe(
            master_df.head(100),
            use_container_width=True
        )

        st.download_button(
            "⬇️ Download Complete Master CSV",
            data=master_df.to_csv(index=False),
            file_name="NIFTY50_COMPLETE_HISTORICAL_DATA.csv",
            mime="text/csv"
        )

        st.download_button(
            "⬇️ Download All Stock Summary",
            data=summary_df.to_csv(index=False),
            file_name="NIFTY50_LATEST_SUMMARY.csv",
            mime="text/csv"
        )

    if failed_stocks:

        with st.expander("Stocks whose data could not be loaded"):

            st.write(failed_stocks)


# =====================================================
# FOOTER
# =====================================================

st.divider()

st.caption(
    "NIFTY 50 Trading Analytics | "
    "Historical data and technical indicators for research. "
    "Market data availability depends on the source."
)
