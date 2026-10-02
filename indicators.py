import pandas as pd
import numpy as np


def add_all_indicators(df):
    """
    Calculate technical indicators for stock price data.
    """

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Normalize column names
    df.columns = [str(c).strip().title() for c in df.columns]

    required = ["Open", "High", "Low", "Close", "Volume"]

    if not all(col in df.columns for col in required):
        return pd.DataFrame()

    for col in required:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    close = df["Close"]
    volume = df["Volume"]

    # Moving averages
    for window in [5, 10, 20, 50, 100, 200]:
        df[f"SMA_{window}"] = close.rolling(
            window=window,
            min_periods=window
        ).mean()

    # RSI 14
    delta = close.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / 14,
        min_periods=14,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / 14,
        min_periods=14,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)

    df["RSI"] = 100 - (100 / (1 + rs))

    df.loc[
        (avg_loss == 0) & (avg_gain > 0),
        "RSI"
    ] = 100

    df.loc[
        (avg_loss == 0) & (avg_gain == 0),
        "RSI"
    ] = 50

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    df["MACD"] = ema12 - ema26

    df["MACD_Signal"] = df["MACD"].ewm(
        span=9,
        adjust=False
    ).mean()

    df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

    # Volume indicators
    df["Volume_MA"] = volume.rolling(20).mean()
    df["Volume_MA20"] = df["Volume_MA"]

    df["Volume_Ratio"] = (
        volume / df["Volume_MA"].replace(0, np.nan)
    )

    # Bollinger Bands
    middle = close.rolling(20).mean()
    std = close.rolling(20).std()

    df["BB_Upper"] = middle + 2 * std
    df["BB_Lower"] = middle - 2 * std

    # Daily return
    df["Daily_Return"] = close.pct_change() * 100

    # Volatility
    df["Volatility_20"] = df["Daily_Return"].rolling(20).std()

    # Breakout conditions
    df["Breakout"] = (
        (close > df["SMA_50"]) &
        (df["Volume_Ratio"] > 1)
    )

    return df


def flag_breakout(df):
    """
    Check whether the latest available row meets
    the configured breakout conditions.
    """

    if df is None or df.empty:
        return False

    if "SMA_50" not in df.columns:
        df = add_all_indicators(df)

    if df.empty:
        return False

    latest = df.iloc[-1]

    required = ["Close", "SMA_50", "Volume_Ratio"]

    if any(
        col not in df.columns or pd.isna(latest[col])
        for col in required
    ):
        return False

    return bool(
        latest["Close"] > latest["SMA_50"]
        and latest["Volume_Ratio"] > 1
    )