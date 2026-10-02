# ============================================================
# NIFTY 50 COMPLETE TRADING ANALYTICS DASHBOARD
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from plotly.subplots import make_subplots
from datetime import datetime

from data_fetcher import get_stock_data, get_nifty50_symbols
from indicators import add_all_indicators, flag_breakout


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="NIFTY 50 Complete Trading Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

[data-testid="stMetric"] {
    background-color: rgba(128,128,128,0.08);
    padding: 16px;
    border-radius: 12px;
    border: 1px solid rgba(128,128,128,0.15);
}

.stTabs [data-baseweb="tab"] {
    font-size: 15px;
    font-weight: 600;
}

[data-testid="stDataFrame"] {
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.title("📈 NIFTY 50 Complete Trading Analytics")

st.caption(
    "Complete Historical Market Database | "
    "Technical Analysis | Market Scanner | "
    "Stock Performance | Data Export"
)


# ============================================================
# SIDEBAR CONTROLS
# ============================================================

st.sidebar.title("⚙️ Dashboard Controls")

if st.sidebar.button(
    "🔄 Refresh All Data",
    use_container_width=True
):
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
    "Show all technical indicators",
    value=True
)

show_data_quality = st.sidebar.checkbox(
    "Show data quality report",
    value=True
)

rows_per_page = st.sidebar.selectbox(
    "Historical table rows per page",
    [100, 250, 500, 1000, 5000],
    index=2
)

st.sidebar.divider()

st.sidebar.info(
    "Data coverage depends on the configured market data provider."
)


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def load_stock_data(symbol):

    try:

        df = get_stock_data(
            symbol,
            period="max"
        )

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

        df = df.replace(
            [np.inf, -np.inf],
            np.nan
        )

        return df

    except Exception:
        return None


# ============================================================
# LOAD SYMBOLS
# ============================================================

symbols = get_nifty50_symbols()

if not symbols:

    st.error("No stock symbols found.")

    st.stop()

st.sidebar.metric(
    "Configured Stocks",
    len(symbols)
)


# ============================================================
# FETCH ALL STOCKS
# ============================================================

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

    progress.progress(
        (i + 1) / len(symbols)
    )

progress.empty()

status.empty()


if not stock_data:

    st.error(
        "No stock data could be loaded. "
        "Check data_fetcher.py, indicators.py, "
        "and your data source."
    )

    st.stop()


# ============================================================
# CREATE MASTER LATEST SUMMARY
# ============================================================

summary = []

for symbol, df in stock_data.items():

    latest = df.iloc[-1]

    previous_close = (
        df["Close"].iloc[-2]
        if len(df) > 1
        else latest["Close"]
    )

    change = (
        latest["Close"] - previous_close
    )

    change_percent = (
        change / previous_close * 100
        if pd.notna(previous_close)
        and previous_close != 0
        else np.nan
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

        "Volume Ratio": latest.get(
            "Volume_Ratio",
            np.nan
        ),

        "MACD": latest.get("MACD", np.nan),

        "MACD Signal": latest.get(
            "MACD_Signal",
            np.nan
        )

    })


summary_df = pd.DataFrame(summary)

summary_df = summary_df.replace(
    [np.inf, -np.inf],
    np.nan
)


# ============================================================
# MARKET METRICS
# ============================================================

total_stocks = len(stock_data)

advancing = int(
    (summary_df["Change"] > 0).sum()
)

declining = int(
    (summary_df["Change"] < 0).sum()
)

unchanged = int(
    (summary_df["Change"] == 0).sum()
)

average_change = summary_df["Change %"].mean()

total_volume = summary_df["Volume"].sum()


# ============================================================
# TOP DASHBOARD METRICS
# ============================================================

st.subheader("📊 Market Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Stocks Loaded",
    total_stocks
)

col2.metric(
    "Advancing",
    advancing
)

col3.metric(
    "Declining",
    declining
)

col4.metric(
    "Average Change",
    f"{average_change:.2f}%"
    if pd.notna(average_change)
    else "N/A"
)

col5, col6, col7, col8 = st.columns(4)

col5.metric(
    "Unchanged",
    unchanged
)

col6.metric(
    "Market Breadth",
    f"{advancing}/{total_stocks}"
)

col7.metric(
    "Total Available Volume",
    f"{total_volume:,.0f}"
)

col8.metric(
    "Failed Data Sources",
    len(failed_stocks)
)


# ============================================================
# DASHBOARD TABS
# ============================================================

tab1, tab2, tab3, tab4, tab5 = st.tabs([

    "📊 Market Overview",

    "🔍 Individual Stock",

    "🚀 Breakout Scanner",

    "📚 Historical Database",

    "⬇️ Complete Data Export"

])


# ============================================================
# TAB 1: MARKET OVERVIEW
# ============================================================

with tab1:

    st.header("Complete NIFTY 50 Market Overview")

    search = st.text_input(
        "🔎 Search stock",
        placeholder="RELIANCE, TCS, SBIN..."
    )

    filtered_summary = summary_df.copy()

    if search:

        filtered_summary = filtered_summary[
            filtered_summary["Symbol"].str.contains(
                search,
                case=False,
                na=False
            )
        ]

    sort_column = st.selectbox(
        "Sort stocks by",
        [
            "Change %",
            "Close",
            "Volume",
            "RSI",
            "Symbol"
        ]
    )

    ascending = st.checkbox(
        "Ascending order",
        value=False
    )

    filtered_summary = filtered_summary.sort_values(
        sort_column,
        ascending=ascending,
        na_position="last"
    )

    st.subheader("All Available Stock Statistics")

    st.dataframe(
        filtered_summary,
        use_container_width=True,
        hide_index=True,
        height=550
    )

    st.download_button(
        "⬇️ Download Market Summary CSV",
        data=filtered_summary.to_csv(index=False),
        file_name="NIFTY50_MARKET_SUMMARY.csv",
        mime="text/csv"
    )

    # --------------------------------------------------------
    # TOP GAINERS
    # --------------------------------------------------------

    st.subheader("📈 Top Gainers")

    gainers = summary_df.nlargest(
        10,
        "Change %"
    )

    st.dataframe(
        gainers,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # TOP DECLINERS
    # --------------------------------------------------------

    st.subheader("📉 Top Decliners")

    decliners = summary_df.nsmallest(
        10,
        "Change %"
    )

    st.dataframe(
        decliners,
        use_container_width=True,
        hide_index=True
    )

    # --------------------------------------------------------
    # PRICE CHANGE CHART
    # --------------------------------------------------------

    st.subheader("Stock Price Change")

    chart_df = summary_df.sort_values(
        "Change %",
        na_position="last"
    )

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
        height=550,
        xaxis_tickangle=-60,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # PERFORMANCE DISTRIBUTION
    # --------------------------------------------------------

    st.subheader("Market Performance Distribution")

    fig = go.Figure()

    fig.add_trace(
        go.Histogram(
            x=summary_df["Change %"].dropna(),
            nbinsx=25,
            name="Returns"
        )
    )

    fig.update_layout(
        title="Distribution of Latest Available Returns",
        xaxis_title="Change (%)",
        yaxis_title="Number of Stocks",
        height=450
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # VOLUME ANALYSIS
    # --------------------------------------------------------

    st.subheader("Volume Comparison")

    volume_df = summary_df.sort_values(
        "Volume",
        ascending=False
    ).head(20)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=volume_df["Symbol"],
            y=volume_df["Volume"],
            name="Volume"
        )
    )

    fig.update_layout(
        title="Top 20 Stocks by Latest Available Volume",
        xaxis_title="Stock",
        yaxis_title="Volume",
        height=450,
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


# ============================================================
# TAB 2: INDIVIDUAL STOCK ANALYSIS
# ============================================================

with tab2:

    st.header("Complete Individual Stock Analysis")

    selected_symbol = st.selectbox(
        "Select a stock",
        list(stock_data.keys())
    )

    df = stock_data[selected_symbol].copy()

    st.subheader(selected_symbol)

    min_date = df.index.min().date()

    max_date = df.index.max().date()

    date_range = st.date_input(
        "Select historical date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if (
        isinstance(date_range, (tuple, list))
        and len(date_range) == 2
    ):

        start_date, end_date = date_range

        filtered_df = df.loc[
            (df.index.date >= start_date)
            &
            (df.index.date <= end_date)
        ].copy()

    else:

        filtered_df = df.copy()

    if filtered_df.empty:

        st.warning(
            "No records available for this date range."
        )

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
            if pd.notna(latest.get("Volume"))
            else "N/A"
        )

        # ----------------------------------------------------
        # PRICE, RSI, VOLUME CHART
        # ----------------------------------------------------

        fig = make_subplots(
            rows=3,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.60, 0.20, 0.20],
            subplot_titles=(
                "Price and Moving Averages",
                "Relative Strength Index",
                "Trading Volume"
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

        if "Volume" in filtered_df.columns:

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
            height=900,
            xaxis_rangeslider_visible=False,
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ----------------------------------------------------
        # MACD CHART
        # ----------------------------------------------------

        if "MACD" in filtered_df.columns:

            st.subheader("MACD Analysis")

            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=filtered_df.index,
                    y=filtered_df["MACD"],
                    name="MACD"
                )
            )

            if "MACD_Signal" in filtered_df.columns:

                fig.add_trace(
                    go.Scatter(
                        x=filtered_df.index,
                        y=filtered_df["MACD_Signal"],
                        name="MACD Signal"
                    )
                )

            fig.update_layout(
                height=400,
                title="MACD and Signal Line"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        # ----------------------------------------------------
        # COMPLETE INDICATOR TABLE
        # ----------------------------------------------------

        st.subheader("Latest Technical Indicators")

        st.dataframe(
            filtered_df.tail(50),
            use_container_width=True,
            height=500
        )

        st.download_button(
            "⬇️ Download Selected Stock History",
            data=filtered_df.to_csv(index=True),
            file_name=f"{selected_symbol}_analysis.csv",
            mime="text/csv"
        )


# ============================================================
# TAB 3: BREAKOUT SCANNER
# ============================================================

with tab3:

    st.header("🚀 Technical Breakout Scanner")

    breakout_results = []

    for symbol, df in stock_data.items():

        try:

            result = flag_breakout(df)

            if result:

                latest = df.iloc[-1]

                breakout_results.append({

                    "Symbol": symbol,

                    "Date": str(df.index[-1].date()),

                    "Close": latest.get(
                        "Close",
                        np.nan
                    ),

                    "SMA 20": latest.get(
                        "SMA_20",
                        np.nan
                    ),

                    "SMA 50": latest.get(
                        "SMA_50",
                        np.nan
                    ),

                    "SMA 200": latest.get(
                        "SMA_200",
                        np.nan
                    ),

                    "RSI": latest.get(
                        "RSI",
                        np.nan
                    ),

                    "Volume Ratio": latest.get(
                        "Volume_Ratio",
                        np.nan
                    ),

                    "MACD": latest.get(
                        "MACD",
                        np.nan
                    )

                })

        except Exception:

            continue

    if breakout_results:

        breakout_df = pd.DataFrame(
            breakout_results
        )

        st.metric(
            "Stocks Matching Breakout Conditions",
            len(breakout_df)
        )

        st.dataframe(
            breakout_df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download Breakout Scanner CSV",
            data=breakout_df.to_csv(index=False),
            file_name="NIFTY50_BREAKOUT_SCANNER.csv",
            mime="text/csv"
        )

    else:
        st.info("No stocks currently satisfy the configured breakout conditions, or the scanner returned no results.")
